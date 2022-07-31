import os
from logging import config as logging_config

from pydantic import BaseSettings, Field

from core.logger import LOGGING


class Settings(BaseSettings):
    project_name: str = Field('billing_app', env='PROJECT_NAME')
    auth_grpc_host: str = Field('localhost', env='AUTH_GRPC_HOST')
    auth_grpc_port: int = Field(50051, env='AUTH_GRPC_PORT')

    db_postgres_host: str = Field('localhost', env='POSTGRES_HOST')
    db_postgres_user: str = Field('postgres', env='POSTGRES_USER')
    db_postgres_password: str = Field('12345', env='POSTGRES_PASSWORD')
    db_postgres_port: int = Field(5432, env='POSTGRES_PORT')
    db_postgres_name: str = Field('billing', env='POSTGRES_DB')

    stripe_key: str = Field('', env='STRIPE_KEY')

    stripe_webhook_secret: str = Field(
        '',
        env='WEBHOOK_SECRET',
    )
    subscription_url: str = Field(
        'http://127.0.0.1:8000/api/v1/subscription',
        env='SUBSCRIPTION_URL',
    )

    auth_api_key: str = Field(
        'key',
        env='AUTH_API_KEY',
    )

    auth_path_url: str = Field(
        'http://127.0.0.1:80/api/v1/user/role',
        env='AUTH_PATH_URL',
    )


    class Config:
        env_file = ".env"


# Применяем настройки логирования
logging_config.dictConfig(LOGGING)

# Корень проекта

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, 'static/')
