from uuid import UUID

from sqlalchemy import select
from functools import lru_cache
from fastapi import Depends

from core.db import get_pg
from core.config import Settings
from databases import Database

from core.stripe_config import get_stripe
from db.sql_model import SubscriptionStatus
from db.sql_model import StripeCustomer as customer_table

from services.prices_service import PriceService, get_price_service
from services.products_service import ProductService, get_products_service

settings = Settings()


class SubscriptionService:

    def __init__(
        self,
        db: Database,
        price_service: PriceService,
        product_service: ProductService,
        stripe_loc,
    ):
        self.db = db
        self.price_service = price_service
        self.product_service = product_service
        self.stripe = stripe_loc

    async def check_user_has_subscription(self, user_id: UUID):
        """Check if current user already has a subscription."""
        get_customer_query = select(customer_table).where(customer_table.user_id == user_id)
        customer = await self.db.fetch_one(get_customer_query)

        if customer and self.stripe.Subscription.list(
            customer=customer.stripe_customer_id,
            status=SubscriptionStatus.active.value,
            limit=1,
        ):
            return customer

    async def create_subscription_session(self, user_id: UUID, product_id: str):
        """Create session to subscribe."""
        prices = await self.price_service.get_all_in_product(product_id)
        price_items = [
            {
                'price': price.stripe_price_id,
                'quantity': 1,
            } for price in prices
        ]

        get_customer_query = select(customer_table).where(customer_table.user_id == user_id)
        customer = await self.db.fetch_one(get_customer_query)
        domain_url = settings.subscription_url

        session_params = {
            "success_url": domain_url + '/success?session_id={CHECKOUT_SESSION_ID}',
            "cancel_url": domain_url + '/canceled',
            "payment_method_types": ['card'],
            "mode": 'subscription',
            "line_items": price_items,
            "metadata": {
                "user_id": user_id,
            }
        }
        if customer:
            session_params["customer"] = customer.stripe_customer_id

        checkout_session = self.stripe.checkout.Session.create(**session_params)
        return checkout_session


@lru_cache()
def get_subscription_service(
    db: Database = Depends(get_pg),
    price_service: PriceService = Depends(get_price_service),
    product_service: ProductService = Depends(get_products_service),
    stripe_loc=Depends(get_stripe),
) -> SubscriptionService:
    return SubscriptionService(db, price_service, product_service, stripe_loc)
