from functools import lru_cache
from uuid import UUID

from databases import Database
from fastapi import Depends
from sqlalchemy import select, and_

from core.config import Settings
from core.db import get_pg
from db.sql_model import (
    BillingHistory as BillingHistoryTable,
    StripeCustomer as StripeCustomerTable,
    Price as PriceTable
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
            BillingHistoryTable.id,
            BillingHistoryTable.created_at,
            PriceTable.name,
            BillingHistoryTable.stripe_subscription_id,
        ]).join(
            StripeCustomerTable, isouter=True
        ).where(
            and_(StripeCustomerTable.user_id == uuid,
                 BillingHistoryTable.subscription_status == 'active')
        ).order_by(
            BillingHistoryTable.created_at.desc()
        )

        result = await self.db.fetch_all(query)
        history = None
        if result:
            history = [UserSubscriptions(
                id=item.id,
                created_at=item.created_at,
                subscription=item.name,
                subscription_id=item.stripe_subscription_id
            ) for item in result]
        return history


@lru_cache()
def get_billing_history_service(
        db: Database = Depends(get_pg),
) -> BillingHistoryService:
    return BillingHistoryService(db)
