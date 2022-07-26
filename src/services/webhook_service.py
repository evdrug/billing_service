import datetime
import uuid

import stripe
from functools import lru_cache
from fastapi import Depends

from core.constants import CUSTOMER_CREATED_EVENT, CUSTOMER_SUBSCRIPTION_CREATED, PAYMENT_SUCCEEDED, PAYMENT_FAILED
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
        customer_id = data['object'].get("customer")
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
        """Invoice paid."""
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
        # TODO SEND REQUEST TO AUTH WITH USER_ID-PERMISSION_ID
        # if success_paid and subscription['status'] == SubscriptionStatus.active.value:
        #     data_to_auth = {
        #         "user_id": user_customer.user_id,
        #         "permission_id": price.permission_id
        #     }
        #     auth_service.send(data_to_auth)
        return subscription_history.dict()

    async def _subscription_created_event(self, data: dict) -> dict:
        """Subscription was created for customer."""
        subscription_data = data['object']

        customer_id = subscription_data['customer']
        user_customer_query = select(customer_table).where(customer_table.stripe_customer_id == customer_id)
        user_customer = await self.db.fetch_one(user_customer_query)

        stripe_price_id = subscription_data['plan']['id']
        price_query = select(price_table).where(price_table.stripe_price_id == stripe_price_id)
        price = await self.db.fetch_one(price_query)

        subscription_history = BillingHistory(
            id=uuid.uuid4(),
            stripe_customer=user_customer.id,
            price=price.id,
            stripe_subscription_id=subscription_data['id'],
            event_type=CUSTOMER_SUBSCRIPTION_CREATED,
            subscription_status=subscription_data['status'],
            created_at=datetime.datetime.now(),
        )
        history_query = insert(billing_history).values(**subscription_history.dict())
        await self.db.execute(history_query)

        return subscription_history.dict()

    async def handling_event(self, event):
        """Handle webhook events."""
        handlers = {
            CUSTOMER_CREATED_EVENT: self._customer_created_event,
            PAYMENT_SUCCEEDED: self._payment_event,
            CUSTOMER_SUBSCRIPTION_CREATED: self._subscription_created_event,
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
