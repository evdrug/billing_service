import datetime
import json
import uuid
import requests

import stripe
from functools import lru_cache
from fastapi import Depends

from core.constants import (
    CUSTOMER_CREATED_EVENT,
    CUSTOMER_SUBSCRIPTION_CREATED,
    PAYMENT_SUCCEEDED,
    PAYMENT_FAILED,
    CUSTOMER_SUBSCRIPTION_UPDATED,
)
from core.db import get_pg
from core.config import Settings
from databases import Database
from db.sql_model import StripeCustomer as customer_table, SubscriptionStatus
from db.sql_model import BillingHistory as billing_history
from db.sql_model import Price as price_table
from sqlalchemy import select, insert

from models.billing_history import BillingHistory
from models.customer import UserCustomer


settings = Settings()
stripe.api_key = settings.stripe_key


class WebhookSubscriptionService:

    def __init__(self, db: Database):
        self.db = db

    async def _customer_created_event(self, data: dict):
        """Map user_id with stripe customer if not exists."""
        customer_id = data['object'].get('customer')
        user_id = data['object']['metadata'].get('user_id')
        get_user_query = select(customer_table).where(customer_table.stripe_customer_id == customer_id)
        if result := await self.db.fetch_one(get_user_query):
            return result
        instance_id = uuid.uuid4()
        user_customer = UserCustomer(
            id=instance_id,
            user_id=user_id,
            stripe_customer_id=customer_id,
        )
        query = insert(customer_table).values(**user_customer.dict())
        await self.db.execute(query)

    async def _payment_event(self, data: dict):
        """Invoice paid. Send subscribtion data to auth."""
        paid_data = data['object']

        success_paid = paid_data['status'] == 'paid' and paid_data['paid'] is True
        customer_id = paid_data['customer']
        user_customer_query = select(customer_table).where(customer_table.stripe_customer_id == customer_id)
        user_customer = await self.db.fetch_one(user_customer_query)

        stripe_price_id = paid_data['lines']['data'][0]['price']['id']
        price_query = select(price_table).where(price_table.stripe_price_id == stripe_price_id)
        price = await self.db.fetch_one(price_query)

        stripe_subscription_id = paid_data['subscription']
        subscription = stripe.Subscription.retrieve(stripe_subscription_id)

        subscription_history = BillingHistory(
            id=uuid.uuid4(),
            stripe_customer=user_customer.id,
            price=price.id,
            stripe_subscription_id=stripe_subscription_id,
            event_type=PAYMENT_SUCCEEDED if success_paid else PAYMENT_FAILED,
            subscription_status=subscription['status'],
            created_at=datetime.datetime.now(),
        )
        history_query = insert(billing_history).values(**subscription_history.dict())
        await self.db.execute(history_query)
        period_end_timestamp = paid_data['period_end']
        paid_to_date = str(datetime.datetime.fromtimestamp(period_end_timestamp).date())

        if success_paid and subscription['status'] == SubscriptionStatus.active.value:
            data_to_auth = {
                'user_id': str(user_customer.user_id),
                'permission_id': 1,
                'paid_to_date': paid_to_date,
            }
            # TODO Move to different service, think about exceptions
            response = requests.post(
                settings.auth_path_url,
                data=json.dumps(data_to_auth),
                headers={'APIKEY': settings.auth_api_key, 'Content-Type': 'application/json'},
            )

        return subscription_history.dict()

    async def _subscription_event(self, data: dict) -> dict:
        """
        Subscription was created, updated, canceled for customer.

        When subscription was updated to a new price plan, then new payment will be charged from next month.
        When subscription was canceled, still available until the end of previous billing period.
        """
        subscription_data = data['object']

        customer_id = subscription_data['customer']
        user_customer_query = select(customer_table).where(customer_table.stripe_customer_id == customer_id)
        user_customer = await self.db.fetch_one(user_customer_query)

        stripe_price_id = subscription_data['plan']['id']
        price_query = select(price_table).where(price_table.stripe_price_id == stripe_price_id)
        price = await self.db.fetch_one(price_query)

        updated_data = data.get('previous_attributes')

        subscription_history = BillingHistory(
            id=uuid.uuid4(),
            stripe_customer=user_customer.id,
            price=price.id,
            stripe_subscription_id=subscription_data['id'],
            event_type=CUSTOMER_SUBSCRIPTION_UPDATED if updated_data else CUSTOMER_SUBSCRIPTION_CREATED,
            subscription_status=subscription_data['status'],
            created_at=datetime.datetime.now(),
            additional_info=json.dumps(updated_data) if updated_data else None,
        )
        history_query = insert(billing_history).values(**subscription_history.dict())
        await self.db.execute(history_query)

        return subscription_history.dict()

    async def handling_event(self, event):
        """Handle webhook events."""
        handlers = {
            CUSTOMER_CREATED_EVENT: self._customer_created_event,
            PAYMENT_SUCCEEDED: self._payment_event,
            CUSTOMER_SUBSCRIPTION_CREATED: self._subscription_event,
            CUSTOMER_SUBSCRIPTION_UPDATED: self._subscription_event,
            PAYMENT_FAILED: self._payment_event,
        }
        data = event['data']
        event_type = event['type']
        if handler := handlers.get(event_type):
            await handler(data)


@lru_cache()
def get_webhook_service(
    db: Database = Depends(get_pg),
) -> WebhookSubscriptionService:
    return WebhookSubscriptionService(db)
