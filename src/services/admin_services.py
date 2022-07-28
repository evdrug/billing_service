from datetime import datetime
from functools import lru_cache
from uuid import UUID

from databases import Database
from fastapi import Depends
from sqlalchemy import select, and_
import stripe

from core.config import Settings
from core.db import get_pg
from db.sql_model import (
    BillingHistory as BillingHistoryTable,
    StripeCustomer as StripeCustomerTable,
    Price as PriceTable,
    Product as ProductTable,
)
from models.history import BillingHistory, UserSubscriptions

settings = Settings()


class BillingHistoryService:
    def __init__(self, db: Database):
        self.db = db

    async def get_user_history(self, uuid: UUID):
        query = select([
            BillingHistoryTable.id,
            BillingHistoryTable.created_at,
            PriceTable.name,
            BillingHistoryTable.stripe_subscription_id,
            BillingHistoryTable.subscription_status,
            BillingHistoryTable.event_type,
            StripeCustomerTable.user_id,
        ]).join(
           StripeCustomerTable, isouter=True
        ).join(
            PriceTable, isouter=True
        ).where(
            StripeCustomerTable.user_id == uuid
        ).order_by(
            BillingHistoryTable.created_at.desc()
        )

        result = await self.db.fetch_all(query)
        history = None
        if result:
            history = [BillingHistory(
                id=item.id,
                created_at=item.created_at,
                subscription=item.name,
                subscription_id=item.stripe_subscription_id,
                subscription_status=item.subscription_status,
                event_type=item.event_type,
                user_id=item.user_id
            ) for item in result]
        return history

    async def get_user_subscriptions(self, uuid: UUID):
        query = select([
            StripeCustomerTable.stripe_customer_id,
        ]).where(
            StripeCustomerTable.user_id == uuid
        )
        stripe.api_key = settings.stripe_key
        stripe_customer = await self.db.fetch_one(query)
        data_dict = {
            'customer': stripe_customer.stripe_customer_id,
            'status': 'all'
        }
        subscriptions = stripe.Subscription.list(**data_dict)

        result = []
        for subscription in subscriptions.data:
            if subscription.status in ['active', 'trialing', 'canceled', 'ended']:
                start_date = datetime.fromtimestamp(subscription.current_period_start).date()
                ended_at = subscription.ended_at if subscription.ended_at else subscription.current_period_end
                end_date = datetime.fromtimestamp(ended_at).date()
                price_id = subscription.plan.id
                query = select([
                    PriceTable.id,
                    PriceTable.name,
                    ProductTable.name,
                ]).join(
                    ProductTable, isouter=True
                ).where(
                    PriceTable.stripe_product_id == price_id # todo price_id
                )
                query_res = await self.db.fetch_one(query)
                result.append(UserSubscriptions(
                    status=subscription.status,
                    start_date=start_date,
                    end_date=end_date,
                    price_id=query_res.id if query_res else None,
                    price_name=query_res.name if query_res else None,
                    product_name=query_res.name if query_res else None,
                ))
        return result

    # async def update_user_subscriptions(self, user_uuid: UUID, price_uuid: UUID):
    #     stripe.api_key = settings.stripe_key


@lru_cache()
def get_billing_history_service(
        db: Database = Depends(get_pg),
) -> BillingHistoryService:
    return BillingHistoryService(db)
