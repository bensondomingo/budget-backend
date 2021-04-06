from typing import List

from pydantic.types import UUID4  # pylint: disable=no-name-in-module
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependecies import (
    async_get_current_user, authenticate_user, create_user,
    get_admin_user, get_current_user, get_db)
from app.services.security import ban_token, create_access_token, oauth2_scheme
from . import models as m, schemas as s

auth_router = APIRouter(prefix='/auth', tags=['Authentication'])
user_router = APIRouter(prefix='/users', tags=['Users'])


@auth_router.post(
    '/signin',
    response_model=s.Token,
    status_code=status.HTTP_202_ACCEPTED)
def signin(user: s.User = Depends(authenticate_user)):
    access_token = create_access_token(data={'sub': user.username})
    token = s.Token(access_token=access_token, token_type='bearer')
    return token


@auth_router.post(
    '/signup',
    response_model=s.Token,
    status_code=status.HTTP_201_CREATED)
def signup(user: s.User = Depends(create_user)):
    access_token = create_access_token(data={'sub': user.username})
    token = s.Token(access_token=access_token, token_type='bearer')
    return token


@auth_router.post('/signout', status_code=status.HTTP_204_NO_CONTENT)
async def signout(token: str = Depends(oauth2_scheme)):
    t = s.BanToken(access_token=token, reason='signout')
    ban_token(t)


@user_router.get('/me', response_model=s.User)
def read_users_me(user: s.User = Depends(get_current_user)):
    return user


@user_router.get('/async/me', response_model=s.User)
async def async_read_users_me(user: s.User = Depends(async_get_current_user)):
    return user


@user_router.get(
    '/', response_model=List[s.User],
    dependencies=[Depends(get_admin_user)],
    status_code=status.HTTP_200_OK)
def read_users(
        skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(m.User).offset(skip).limit(limit).all()


@user_router.delete(
    '/{user_id}',
    dependencies=[Depends(get_admin_user)],
    status_code=status.HTTP_204_NO_CONTENT)
def remove_user(user_id: UUID4, db: Session = Depends(get_db)):
    db_user = db.query(m.User).filter_by(id=user_id.hex).first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    db.delete(db_user)
    db.commit()
