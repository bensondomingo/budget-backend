from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.config import settings


engine = create_engine(settings.DB_URI)
async_engine = create_async_engine(
    settings.DB_ASYNC_URI, future=True, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = sessionmaker(
    async_engine, expire_on_commit=False, class_=AsyncSession)


Base = declarative_base()
