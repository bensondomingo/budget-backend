from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.schemas import User, UserCreate
from app.database.crud import (create_user, get_users, get_user_by_username)
from app.dependecies import get_db, get_current_user

router = APIRouter(tags=['users'], dependencies=[Depends(get_db)])


@router.post('/users/', response_model=User)
def add_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(
            status_code=400, detail="username already registered")
    return create_user(db, user)


@router.get('/users/', response_model=List[User])
def get_all_users(
        skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = get_users(db=db, skip=skip, limit=limit)
    return users


@router.get('/users/me', response_model=User)
def read_users_me(user: User = Depends(get_current_user)):
    return user
