from sqlalchemy import create_engine, future
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.config import settings


DB_URI_SYNC = 'postgresql+psycopg2://{}:{}@{}/{}'.format(
    settings.DB_USER, settings.DB_PASSWORD, settings.DB_HOST, settings.DB_NAME)

DB_URI_ASYNC = 'postgresql+asyncpg://{}:{}@{}/{}'.format(
    settings.DB_USER, settings.DB_PASSWORD, settings.DB_HOST, settings.DB_NAME)


engine = create_engine(DB_URI_SYNC, future=True, echo=settings.DEBUG_MODE)
async_engine = create_async_engine(
    DB_URI_ASYNC, future=True, echo=settings.DEBUG_MODE)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = sessionmaker(
    async_engine, expire_on_commit=False, class_=AsyncSession)


Base = declarative_base()
