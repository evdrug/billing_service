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
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.config import Settings

settings = Settings()
# engine = create_async_engine(settings.db_postgress_url, echo=True, future=True)
#
#
# async def init_db():
#     async with engine.begin() as conn:
#         # await conn.run_sync(SQLModel.metadata.drop_all)
#         await conn.run_sync(SQLModel.metadata.create_all)
#
#
# async def get_session() -> AsyncSession:
#     async_session = sessionmaker(
#         engine, class_=AsyncSession, expire_on_commit=False
#     )
#     async with async_session() as session:
#         yield session

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

