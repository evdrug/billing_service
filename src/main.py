from databases import Database
from fastapi import FastAPI, Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy import select, insert

from api.v1 import products, prices, admin
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


#
# @app.on_event('startup')
# async def startup():
#     # Подключаемся к базам при старте сервера
#     # Подключиться можем при работающем event-loop
#     # Поэтому логика подключения происходит в асинхронной функции
#     redis.redis = aioredis.from_url(
#         f'redis://{config.REDIS_HOST}:{config.REDIS_PORT}'
#     )
#     elastic.es = AsyncElasticsearch(
#         hosts=[f'http://{config.ELASTIC_HOST}:{config.ELASTIC_PORT}'],
#         http_auth=(
#             config.ELASTIC_USER,
#             config.ELASTIC_PASSWORD
#         )
#     )
#
#     grpc_init.grpc_auth = grpc.aio.insecure_channel(
#         f'{config.AUTH_GRPC_HOST}:{config.AUTH_GRPC_PORT}'
#     )
#
#
# @app.on_event('shutdown')
# async def shutdown():
#     # Отключаемся от баз при выключении сервера
#     await redis.redis.close()
#     await elastic.es.close()
#     await grpc_init.grpc_auth.close()
#

app.include_router(products.router, prefix='/api/v1/products')
app.include_router(prices.router, prefix='/api/v1/prices')
app.include_router(admin.router, prefix='/api/v1/admin')
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
