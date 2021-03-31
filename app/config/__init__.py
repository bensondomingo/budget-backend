# pylint: disable=missing-class-docstring
from pydantic import BaseSettings


class CommonSettings(BaseSettings):
    APP_NAME: str = 'Budget Buddy Backend'
    DEBUG_MODE: bool = True


class ServerSettings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000


class DatabaseSettings(BaseSettings):
    DB_NAME: str = 'budget'
    DB_HOST: str = 'localhost'
    DB_PORT: int = 27017
    DB_URI: str = 'sqlite:///./db.sqlite3'


class SecuritySettings(BaseSettings):
    SECRET_KEY: str = '08a9cc52c109039e'
    SECRET_ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
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
