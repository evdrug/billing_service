import grpc
import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from starlette.staticfiles import StaticFiles

from api.v1 import products, subscription, prices, admin
from core import db
from core import stripe_config
from core.config import Settings, STATIC_DIR
from core.db import db_init
from core.stripe_config import stripe_init
from grpc_auth_client import client
from grpc_auth_client.protos import auth_pb2_grpc

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


app.include_router(products.router, prefix='/api/v1/products')
app.include_router(prices.router, prefix='/api/v1/prices')
app.include_router(admin.router, prefix='/api/v1/admin')
app.include_router(subscription.router, prefix='/api/v1/subscription')
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=8000,
    )
