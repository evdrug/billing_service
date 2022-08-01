import uuid
from functools import lru_cache
from typing import Optional

from databases import Database
from fastapi import Depends
from sqlalchemy import select, insert, update, and_

from core.config import Settings
from core.db import get_pg
from core.stripe_config import get_stripe
from db.sql_model import Price as PriceSql
from models.prices import TypePrice, Price, TypeRecurring
from services.products_service import ProductService, get_products_service

settings = Settings()


class PriceService:
    def __init__(self, db: Database, products_service: ProductService, stripe_loc):
        self.db = db
        self.products_service = products_service
        self.stripe = stripe_loc

    async def get_all_in_product(self, uuid):
        query = select(PriceSql).filter(and_(PriceSql.product_id == uuid, PriceSql.active == True))
        result = await self.db.fetch_all(query)
        prices = None

        if result:
            prices = [Price.from_orm(item) for item in result]
        return prices

    async def get_one(self, uuid: str) -> Optional[Price]:
        query = select(PriceSql).where(PriceSql.id == uuid)
        result = await self.db.fetch_one(query)
        price = None
        if result:
            price = Price.from_orm(result)
        return price

    async def create(
            self,
            name: str,
            product_id: str,
            permission_id: int,
            unit_amount: int, currency: str,
            interval: str,
            interval_count: int,
            type_price: TypePrice,
            using_type: TypeRecurring
    ):
        product = await self.products_service.get_one(product_id)

        new_id = uuid.uuid4()
        price = Price(
            id=new_id,
            product_id=product.id,
            name=name,
            active=True,
            type=type_price.value,
            unit_amount=unit_amount,
            currency=currency,
            interval=interval.value if interval else None,
            interval_count=interval_count,
            using_type=using_type.value if using_type else None,
            permission_id=permission_id,
            stripe_product_id=product.stripe_product_id,
        )

        # Todo проверить на наличие прайса
        price_new = self.stripe.Price.create(
            unit_amount=price.unit_amount,
            currency=price.currency,
            recurring={
                'interval': price.interval,
                'interval_count': price.interval_count,
                'usage_type': price.using_type
            },
            product=price.stripe_product_id,
        )

        price.stripe_price_id = price_new.id
        price_base = Price(**price.dict())
        query = insert(PriceSql).values(**price_base.dict())
        await self.db.execute(query)
        return price

    # async def edit(self, uuid, name):
    #     # Todo надо определиться что можем править
    #     price_old = await self.get_one(uuid)
    #     self.stripe.Price.modify(
    #         price_old.stripe_price_id,
    #         name=name,
    #     )
    #     query = update(PriceSql).where(PriceSql.id == uuid).values(name=name)
    #     await self.db.execute(query)
    #     result = await self.get_one(uuid)
    #     return result

    async def delete(self, uuid):
        price_old = await self.get_one(uuid)
        self.stripe.Price.modify(
            price_old.stripe_price_id,
            active=False,
        )
        query = update(PriceSql).where(PriceSql.id == uuid).values(active=False)
        await self.db.execute(query)


@lru_cache()
def get_price_service(
        db: Database = Depends(get_pg),
        products_service: ProductService = Depends(get_products_service),
        stripe_loc=Depends(get_stripe)
) -> PriceService:
    return PriceService(db, products_service, stripe_loc)
