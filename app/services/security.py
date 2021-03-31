from datetime import datetime, timedelta
from typing import Optional

from jose import jwt
from passlib.context import CryptContext

from app.config import settings

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
