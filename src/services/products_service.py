import uuid
from datetime import datetime
from functools import lru_cache

from databases import Database
from fastapi import Depends
from sqlalchemy import select, insert, update, and_

from core.config import Settings
from core.db import get_pg
from core.stripe_config import get_stripe
from db.sql_model import Product as Product_sql
from models.products import Product

settings = Settings()


class ProductService:
    def __init__(self, db: Database, stripe_loc):
        self.db = db
        self.stripe = stripe_loc

    async def get_all(self):
        query = select(Product_sql).where(Product_sql.active == True)
        result = await self.db.fetch_all(query)
        products = None
        if result:
            products = [Product.from_orm(item) for item in result]
        return products

    async def get_one(self, uuid: str):
        query = select(Product_sql).where(Product_sql.id == uuid)
        result = await self.db.fetch_one(query)
        product = None
        if result:
            product = Product.from_orm(result)
        return product

    async def check_product(self, name):
        query = select(Product_sql).filter(
            and_(Product_sql.name == name, Product_sql.active == True)
        )
        result = await self.db.fetch_one(query)
        return result

    async def create(self, name: str):

        product_new = self.stripe.Product.create(name=name)

        new_id = uuid.uuid4()
        product = Product(
            id=new_id,
            stripe_product_id=product_new.id,
            name=product_new.name,
            description=product_new.description,
            created_at=datetime.fromtimestamp(product_new.created),
            updated_at=datetime.fromtimestamp(product_new.updated),
            active=product_new.active
        )
        query = insert(Product_sql).values(**product.dict())
        await self.db.execute(query)
        return Product(**product.dict())

    async def edit(self, uuid, name):
        product_old = await self.get_one(uuid)
        self.stripe.Product.modify(
            product_old.stripe_product_id,
            name=name,
        )
        query = update(Product_sql).where(Product_sql.id == uuid).values(name=name)
        await self.db.execute(query)
        result = await self.get_one(uuid)
        return result

    async def delete(self, uuid):
        product_old = await self.get_one(uuid)
        self.stripe.Product.modify(
            product_old.stripe_product_id,
            active=False,
        )
        query = update(Product_sql).where(Product_sql.id == uuid).values(active=False)
        await self.db.execute(query)


@lru_cache()
def get_products_service(
        db: Database = Depends(get_pg),
        stripe_loc=Depends(get_stripe)
) -> ProductService:
    return ProductService(db, stripe_loc)
