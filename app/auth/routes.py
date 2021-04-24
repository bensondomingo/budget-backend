from typing import Sequence
from pydantic.types import UUID4  # pylint: disable=no-name-in-module
from fastapi.exceptions import HTTPException
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.future import select
from aioredis import Redis

from app.dependecies import (authenticate_user, create_user,
                             get_admin_user, get_current_user, get_async_db)
from app.services.security import ban_token, create_access_token, oauth2_scheme
from app.auth import models as um
from . import schemas as s

auth_router = APIRouter(prefix='/auth', tags=['Authentication'])
user_router = APIRouter(prefix='/users', tags=['Users'])


@auth_router.post(
    '/signin',
    response_model=s.Token,
    status_code=status.HTTP_202_ACCEPTED)
async def signin(user: s.User = Depends(authenticate_user)):
    access_token = create_access_token(data={'sub': user.username})
    token = s.Token(access_token=access_token, token_type='bearer')
    return token


@auth_router.post(
    '/signup',
    response_model=s.Token,
    status_code=status.HTTP_201_CREATED)
async def signup(user: s.User = Depends(create_user)):
    access_token = create_access_token(data={'sub': user.username})
    token = s.Token(access_token=access_token, token_type='bearer')
    return token


@auth_router.post('/signout', status_code=status.HTTP_204_NO_CONTENT)
async def signout(request: Request, token: str = Depends(oauth2_scheme)):
    t = s.BanToken(access_token=token, reason='signout')
    banned_token_registry: Redis = request.app.redis
    await ban_token(t, banned_token_registry)


@user_router.get('/me', response_model=s.User)
async def read_users_me(user: s.User = Depends(get_current_user)):
    return user


@user_router.get(
    '/', response_model=Sequence[s.User],
    dependencies=[Depends(get_admin_user)],
    status_code=status.HTTP_200_OK)
async def read_users(
        skip: int = 0, limit: int = 100,
        db: AsyncSession = Depends(get_async_db)):
    stmt = select(um.User).offset(skip).limit(limit)
    return [row.User for row in (await db.execute(stmt)).all()]


@user_router.delete(
    '/{user_id}',
    dependencies=[Depends(get_admin_user)],
    status_code=status.HTTP_204_NO_CONTENT)
async def remove_user(
        user_id: UUID4, db: AsyncSession = Depends(get_async_db)):
    stmt = select(um.User).where(um.User.id == user_id)
    result = (await db.execute(stmt)).one_or_none()
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    user = result.User

    await db.delete(user)
    await db.flush()
    await db.commit()
