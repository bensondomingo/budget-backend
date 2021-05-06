""" Project level dependencies lives here """
from typing import Union

from aioredis import Redis
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .auth import models as um, schemas as us
from .config import settings
from .core.database import AsyncSessionLocal, SessionLocal
from .services.security import (
    create_access_token, oauth2_scheme, Password, Payload)


def get_db():
    """
    https://fastapi.tiangolo.com/tutorial/sql-databases/#create-a-dependency
    """
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


async def get_async_db():
    db_session = AsyncSessionLocal()
    try:
        yield db_session
    finally:
        await db_session.close()


async def get_current_user(
        request: Request,
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_async_db)) -> us.User:

    # Ensure that token was not banned, else raise credential_exception
    redis: Redis = request.app.redis
    if await redis.exists(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    # Ensure user is a valid db record
    try:
        payload = jwt.decode(token, settings.SECRET_KEY,
                             settings.SECRET_ALGORITHM)
        username: Union[str, None] = payload.get('sub')
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    stmt = select(um.User).where(um.User.username == username)
    result = (await db.execute(stmt)).one_or_none()
    if result is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return result.User


def get_admin_user(user: us.User = Depends(get_current_user)) -> us.User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return user


async def authenticate_user(
        db: AsyncSession = Depends(get_async_db),
        form_data: OAuth2PasswordRequestForm = Depends()) -> str:
    username = form_data.username
    password = form_data.password
    exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

    stmt = select(um.User).where(um.User.username == username)
    result = (await db.execute(stmt)).one_or_none()
    if result is None:
        raise exception

    db_user: um.User = result.User
    if not Password.verify(password, db_user.password):
        raise exception
    payload = Payload(uid=str(db_user.id), sub=db_user.username)
    return create_access_token(payload)


async def create_user(
        user: us.UserCreate,
        db: AsyncSession = Depends(get_async_db)) -> us.User:
    stmt = select(um.User).\
        where(or_(
            um.User.username == user.username,
            um.User.email == user.email))
    result = (await db.execute(stmt)).fetchone()
    if result is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="username and/or email is not available")

    user.password = Password.hash(user.password)
    db_user = um.User(**user.dict(exclude={'password2'}))
    db.add(db_user)
    await db.commit()
    return db_user
