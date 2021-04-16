from datetime import datetime, timedelta

from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from aioredis import Redis

# from app import banned_token_registry
from app.config import settings
from app.auth import schemas as s
from app.errors import credentials_exception

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/signin')

pwd_context = CryptContext(
    schemes=[settings.PWD_HASH_SCHEME], deprecated='auto')


class Password:
    """ Password hashing and verification """

    @classmethod
    def hash(cls, plain: str) -> str:
        """ Hash plain password using selected scheme """
        return pwd_context.hash(plain)

    @classmethod
    def verify(cls, plain: str, hashed: str) -> bool:
        """ Verify if plain password matched with hashed password """
        return pwd_context.verify(plain, hashed)


def create_access_token(data: dict):
    payload = data.copy()
    payload.update({'exp': datetime.utcnow() +
                   timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)})
    token = jwt.encode(payload, settings.SECRET_KEY, settings.SECRET_ALGORITHM)
    return token


async def ban_token(token: s.BanToken, banned_token_registry: Redis):
    if await banned_token_registry.exists(token.access_token):
        raise credentials_exception
    try:
        payload = jwt.decode(token.access_token, settings.SECRET_KEY,
                             settings.SECRET_ALGORITHM)
    except JWTError:
        raise credentials_exception
    exp_ts = payload.get('exp', datetime.now().timestamp())
    td = datetime.fromtimestamp(exp_ts) - datetime.now()
    await banned_token_registry.setex(
        token.access_token, td.seconds, token.reason)
