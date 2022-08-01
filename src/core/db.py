# import os
#
# from sqlmodel import SQLModel
#
# from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
# from sqlalchemy.orm import sessionmaker
#
from typing import Optional

import databases
import sqlalchemy
from databases import Database
from sqlalchemy.ext.asyncio import create_async_engine

from core.config import Settings

settings = Settings()

pg: Optional[Database] = None
db_postgres_url: str = 'postgresql+asyncpg://{}:{}@{}:{}/{}'.format(
    settings.db_postgres_user,
    settings.db_postgres_password,
    settings.db_postgres_host,
    settings.db_postgres_port,
    settings.db_postgres_name
)
engine = create_async_engine(db_postgres_url, echo=True, future=True)

metadata = sqlalchemy.MetaData()


def db_init():
    database = databases.Database(db_postgres_url)
    return database


async def get_pg() -> Database:
    return pg
