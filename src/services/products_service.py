import uuid
from datetime import datetime
from functools import lru_cache

import stripe
from databases import Database
from fastapi import Depends
from sqlalchemy import select, insert, update, delete

from core.config import Settings
from core.db import get_pg
from db.sql_model import Product as Product_sql
from models.products import Product

settings = Settings()


class ProductService:
    def __init__(self, db: Database):
        self.db = db

    async def get_all(self):
        query = select(Product_sql)
        result = await self.db.fetch_all(query)
        products = None
        if result:
            products = [Product(
                id=item.id,
                stripe_product_id=item.stripe_product_id,
                name=item.name,
                description=item.description,
                created_at=item.created_at,
                updated_at=item.updated_at
            ) for item in result]
        return products

    async def get_one(self, uuid: str):
        query = select(Product_sql).where(Product_sql.id == uuid)
        result = await self.db.fetch_one(query)
        product = None
        if result:
            product = Product(
                id=result.id,
                stripe_product_id=result.stripe_product_id,
                name=result.name,
                description=result.description,
                created_at=result.created_at,
                updated_at=result.updated_at
            )
        return product

    async def check_product(self, name):
        query = select(Product_sql).where(Product_sql.name == name)
        result = await self.db.fetch_one(query)
        return result

    async def create(self, name: str):

        stripe.api_key = settings.stripe_key
        product_new = stripe.Product.create(name=name)

        new_id = uuid.uuid4()
        product = Product(
            id=new_id,
            stripe_product_id=product_new.id,
            name=product_new.name,
            description=product_new.description,
            created_at=datetime.fromtimestamp(product_new.created),
            updated_at=datetime.fromtimestamp(product_new.updated)
        )
        query = insert(Product_sql).values(**product.dict())
        await self.db.execute(query)
        return Product(**product.dict())

    async def edit(self, uuid, name):
        product_old = await self.get_one(uuid)
        stripe.api_key = settings.stripe_key
        result = stripe.Product.modify(
            product_old.stripe_product_id,
            name=name,
        )
        query = update(Product_sql).where(Product_sql.id == uuid).values(name=name)
        await self.db.execute(query)
        result = await self.get_one(uuid)
        return result

    async def delete(self, uuid):
        product_old = await self.get_one(uuid)
        stripe.api_key = settings.stripe_key
        stripe.Product.delete(product_old.stripe_product_id)
        query = delete(Product_sql).where(Product_sql.id == uuid)
        await self.db.execute(query)


@lru_cache()
def get_products_service(
        db: Database = Depends(get_pg),
) -> ProductService:
    return ProductService(db)
