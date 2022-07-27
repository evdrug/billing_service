from databases import Database
from fastapi import FastAPI, Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy import select, insert
import grpc

from api.v1 import products, prices
from core import db
from core.config import Settings
from core.db import db_init, get_pg
from core import stripe_config
from core.stripe_config import stripe_init
from db.sql_model import Price, Product
from grpc_auth_client.protos import auth_pb2_grpc
from grpc_auth_client import client

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
    stripe_config.stripe_loc = stripe_init()
    client.channel = grpc.aio.insecure_channel(
        f'{settings.auth_grpc_host}:{settings.auth_grpc_port}')
    client.stub = auth_pb2_grpc.AuthStub(client.channel)
    await db.pg.connect()


@app.on_event("shutdown")
async def shutdown():
    await client.channel.close()
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
