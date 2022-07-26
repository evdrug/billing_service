from uuid import UUID

import stripe
from functools import lru_cache
from fastapi import Depends

from core.db import get_pg
from core.config import Settings
from databases import Database
from db.sql_model import StripeCustomer as customer_table

from sqlalchemy import select
from services.prices_service import PriceService, get_price_service


settings = Settings()
stripe.api_key = settings.stripe_key


class SubscriptionService:

    def __init__(self, db: Database, price_service: PriceService):
        self.db = db
        self.price_service = price_service

    async def check_user_has_subscription(self, user_id: UUID) -> bool:
        """Check if current user already has a subscription."""
        get_customer_query = select(customer_table).where(customer_table.user_id == user_id)
        customer = await self.db.fetch_one(get_customer_query)

        if customer and stripe.Subscription.list(customer=customer.stripe_customer_id, limit=1):
            return True

        return False

    async def create_subscription_session(self, user_id: UUID, price_id: str):
        """Create session to subscribe."""
        price = await self.price_service.get_one(price_id)
        price_item = [
            {
                'price': price.stripe_price_id,
                'quantity': 1,
            },
        ]

        get_customer_query = select(customer_table).where(customer_table.user_id == user_id)
        customer = await self.db.fetch_one(get_customer_query)
        domain_url = settings.subscription_url

        session_params = {
            "success_url": domain_url + '/success?session_id={CHECKOUT_SESSION_ID}',
            "cancel_url": domain_url + '/canceled',
            "payment_method_types": ['card'],
            "mode": 'subscription',
            "line_items": price_item,
            "metadata": {
                "user_id": user_id,
            }
        }
        if customer:
            session_params["customer"] = customer.stripe_customer_id

        checkout_session = stripe.checkout.Session.create(**session_params)
        return checkout_session


@lru_cache()
def get_subscription_service(
    db: Database = Depends(get_pg),
    price_service: PriceService = Depends(get_price_service),
) -> SubscriptionService:
    return SubscriptionService(db, price_service)
