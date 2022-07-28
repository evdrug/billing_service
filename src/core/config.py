import os
from logging import config as logging_config

from pydantic import BaseSettings, Field

from core.logger import LOGGING


class Settings(BaseSettings):
    project_name: str = Field('billing_app', env='PROJECT_NAME')
    auth_grpc_host: str = Field('auth_grpc', env='AUTH_GRPC_HOST')
    auth_grpc_port: int = Field(5005, env='AUTH_GRPC_PORT')

    db_postgres_host: str = Field('localhost', env='POSTGRES_HOST')
    db_postgres_user: str = Field('postgres', env='POSTGRES_USER')
    db_postgres_password: str = Field('12345', env='POSTGRES_PASSWORD')
    db_postgres_port: int = Field(5432, env='POSTGRES_PORT')
    db_postgres_name: str = Field('billing', env='POSTGRES_DB')

    stripe_key: str = Field('', env='STRIPE_KEY')

    class Config:
        env_file = ".env"


# Применяем настройки логирования
logging_config.dictConfig(LOGGING)

# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))