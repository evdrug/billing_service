from datetime import datetime
from functools import lru_cache
from http import HTTPStatus
from uuid import UUID
from functools import wraps

from databases import Database
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy import select, and_

from core.config import Settings
from core.db import get_pg
from core.stripe_config import get_stripe
from db.sql_model import (
    BillingHistory as BillingHistoryTable,
    StripeCustomer as StripeCustomerTable,
    Price as PriceTable,
    Product as ProductTable,
)
from models.history import BillingHistory, UserSubscriptions

settings = Settings()


class BillingHistoryService:
    def __init__(self, db: Database, stripe_loc):
        self.db = db
        self.stripe = stripe_loc

    async def get_user_history(self, uuid: UUID):
        query = select([
            BillingHistoryTable.id,
            BillingHistoryTable.created_at,
            ProductTable.name,
            PriceTable.name.label('price'),
            BillingHistoryTable.stripe_subscription_id,
            BillingHistoryTable.subscription_status,
            BillingHistoryTable.event_type,
            StripeCustomerTable.user_id,
        ]).join(
           StripeCustomerTable, isouter=True
        ).join(
            PriceTable, isouter=True
        ).join(
            ProductTable, isouter=True
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
                product=item.name,
                price=item.price,
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
        stripe_customer = await self.db.fetch_one(query)
        if not stripe_customer:
            return None
        data_dict = {
            'customer': stripe_customer.stripe_customer_id,
            'status': 'all'
        }
        subscriptions = self.stripe.Subscription.list(**data_dict)

        result = []
        for subscription in subscriptions.data:
            if subscription.status in ['active', 'trialing',
                                       'canceled', 'ended']:
                start_date = datetime.fromtimestamp(
                    subscription.current_period_start
                ).date()
                ended_at = (subscription.ended_at
                            if subscription.ended_at
                            else subscription.current_period_end)
                end_date = datetime.fromtimestamp(ended_at).date()
                price_id = subscription.plan.id
                query = select([
                    PriceTable.id,
                    PriceTable.name.label('price'),
                    ProductTable.name,
                ]).join(
                    ProductTable, isouter=True
                ).where(
                    PriceTable.stripe_price_id == price_id
                )
                query_res = await self.db.fetch_one(query)
                result.append(UserSubscriptions(
                    status=subscription.status,
                    start_date=start_date,
                    end_date=end_date,
                    subscription_id=subscription.id,
                    price_id=query_res.id if query_res else None,
                    price_name=query_res.price if query_res else None,
                    product_name=query_res.name if query_res else None,
                ))
        return result

    async def update_user_subscriptions(
            self, user_uuid: UUID, price_uuid: UUID, subscription_id: str
    ):
        query_check = select(
            BillingHistoryTable.id,
            ).join(
           StripeCustomerTable, isouter=True
        ).where(
            and_(
                StripeCustomerTable.user_id == user_uuid,
                BillingHistoryTable.stripe_subscription_id == subscription_id,
                BillingHistoryTable.subscription_status == 'active'
            )
        ).order_by(
            BillingHistoryTable.created_at.desc()
        )
        user_history = await self.db.fetch_one(query_check)

        if not user_history:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='This user did not have the specified subscription.'
            )
        subscription = self.stripe.Subscription.retrieve(subscription_id)
        query = select(
            PriceTable.stripe_price_id
        ).where(
            PriceTable.id == price_uuid
        )
        stripe_price = await self.db.fetch_one(query)

        self.stripe.Subscription.modify(
            subscription.id,
            cancel_at_period_end=False,
            proration_behavior='always_invoice',
            items=[{
                'id': subscription['items']['data'][0].id,
                'price': stripe_price.stripe_price_id
            }]
        )
        return 'Subscription change request sent successfully.'


@lru_cache()
def get_billing_history_service(
        db: Database = Depends(get_pg),
        stripe_loc=Depends(get_stripe)
) -> BillingHistoryService:
    return BillingHistoryService(db, stripe_loc)


def superuser_required(fn):
    @wraps(fn)
    async def wrapper(permissions, *args, **kwargs):
        if settings.auth_superuser_permission in permissions:
            return await fn(*args, **kwargs)
        else:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail='This action is only available for superuser.'
            )

    return wrapper
