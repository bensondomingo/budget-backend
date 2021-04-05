from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic.types import UUID4
from sqlalchemy.orm import Session
from starlette import status

from app.database import models as m
from app.database.schemas import User, UserCreate
from app.database.crud import create_user, get_user_by_username
from app.dependecies import get_admin_user, get_db, get_current_user

router = APIRouter(
    prefix='/users', tags=['users'], dependencies=[Depends(get_db)])


@router.post('/', response_model=User, status_code=status.HTTP_201_CREATED)
def add_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(
            status_code=400, detail="username already registered")
    return create_user(db, user)


@router.get('/me', response_model=User)
def read_users_me(user: User = Depends(get_current_user)):
    return user


@router.get(
    '/', response_model=List[User],
    dependencies=[Depends(get_admin_user)],
    status_code=status.HTTP_200_OK)
def read_users(
        skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(m.User).offset(skip).limit(limit).all()


@router.delete(
    '/{user_id}',
    dependencies=[Depends(get_admin_user)],
    status_code=status.HTTP_204_NO_CONTENT)
def remove_user(user_id: UUID4, db: Session = Depends(get_db)):
    db_user = db.query(m.User).filter_by(id=user_id.hex).first()
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    db.delete(db_user)
    db.commit()
