from pydantic import BaseSettings, Field


class CommonSettings(BaseSettings):
    APP_NAME: str = 'Budget Buddy Backend'
    DEBUG_MODE: bool = True


class ServerSettings(BaseSettings):
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000


class DatabaseSettings(BaseSettings):
    DB_NAME: str = Field('db', env='POSTGRES_DB')
    DB_USER: str = Field('user', env='POSTGRES_USER')
    DB_PASSWORD: str = Field('pw', env='POSTGRES_PASSWORD')
    DB_HOST: str = Field('host', env='POSTGRES_HOST')
    DB_PORT: int = Field(5432, env='POSTGRES_PORT')


class SecuritySettings(BaseSettings):
    SECRET_KEY: str = '681eea7702646659743b8575f37bb558'
    SECRET_ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    PWD_HASH_SCHEME: str = 'bcrypt'


class RedisSettings(BaseSettings):
    REDIS_HOST: str = 'redis'
    REDIS_PORT: int = 6379
    REDIS_BANNED_TOKEN_REGISTRY_DB: int = 1


class Settings(CommonSettings,
               ServerSettings,
               DatabaseSettings,
               SecuritySettings,
               RedisSettings):
    """
    Project settings. https://pydantic-docs.helpmanual.io/usage/settings/
    """


settings = Settings()

__all__ = ('settings',)
