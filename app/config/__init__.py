# pylint: disable=missing-class-docstring
from pydantic import BaseSettings


class CommonSettings(BaseSettings):
    APP_NAME: str = 'Budget Buddy Backend'
    DEBUG_MODE: bool = True


class ServerSettings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000


class DatabaseSettings(BaseSettings):
    DB_NAME: str = 'budget-dev'
    DB_HOST: str = 'db'
    DB_PORT: int = 5432
    DB_URI: str = 'postgresql+psycopg2://root:secret@db/budget-dev'
    DB_ASYNC_URI: str = 'postgresql+asyncpg://root:secret@db/budget-dev'


class SecuritySettings(BaseSettings):
    SECRET_KEY: str = '08a9cc52c109039e'
    SECRET_ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    PWD_HASH_SCHEME: str = 'bcrypt'


class Settings(CommonSettings,
               ServerSettings,
               DatabaseSettings,
               SecuritySettings):
    """
    Project settings. https://pydantic-docs.helpmanual.io/usage/settings/
    """


settings = Settings()

__all__ = ('settings',)
