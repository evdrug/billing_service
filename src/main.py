import uvicorn
from databases import Database
from fastapi import FastAPI, Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy import select, insert
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from api.v1 import products, subscription
from api.v1 import products, prices
from core import db
from core.config import Settings
from core.db import db_init, get_pg
from db.sql_model import Price, Product

settings = Settings()

app = FastAPI(
    # Конфигурируем название проекта. Оно будет отображаться в документации
    title=f'{settings.project_name}',
    # Адрес документации в красивом интерфейсе
    docs_url='/api/openapi',
    # Адрес документации в формате OpenAPI
    openapi_url='/api/openapi.json',
    default_response_class=ORJSONResponse,
    description='billing',
    version='1.0.0',
)


@app.on_event("startup")
async def startup():
    db.pg = db_init()
    await db.pg.connect()


@app.on_event("shutdown")
async def shutdown():
    await db.pg.disconnect()


app.include_router(products.router, prefix='/api/v1/products')
app.include_router(prices.router, prefix='/api/v1/prices')
# app.include_router(genres.router, prefix='/api/v1/genres')
# @app.get("/")
# async def root(db: Database = Depends(get_pg)):
#     print(db)
#     print(Price)
#     query = select(Product)
#     res = await db.fetch_all(query)
#     print(list(res[0].keys()))
#     print(list(res[0].values()))
#     price = Price()
#     price.id='f0508592-262e-425b-b1cd-57828ebd98c4'
#     price.stripe_product_id='f0508592-262e-425b-b1cd-57828ebd97c4'
#     price.name='tttttt'
#     price.description='tttttt'
#     print(insert(Price))
#     # db.execute(insert(price))
#     # prod = Product(id=)
#     return {"message": "Hello World1"}
app.include_router(subscription.router, prefix='/api/v1/subscription')
app.mount("/static", StaticFiles(directory=subscription.static_dir), name="static")


if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=8000,
    )