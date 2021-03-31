""" Project level dependencies lives here """
from typing import Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from .database.engine import SessionLocal
from .database import schemas as s
from .database import models as m
from .services.security import Password
from .config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/signin')


def get_db():
    """
    https://fastapi.tiangolo.com/tutorial/sql-databases/#create-a-dependency
    """

    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)) -> s.User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"})

    try:
        payload = jwt.decode(token, settings.SECRET_KEY,
                             settings.SECRET_ALGORITHM)
        username: Union[str, None] = payload.get('sub')
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    db_user = db.query(m.User).filter(m.User.username == username).first()
    if db_user is None:
        raise credentials_exception
    return s.User.from_orm(db_user)


def authenticate_user(
        db: Session = Depends(get_db),
        form_data: OAuth2PasswordRequestForm = Depends()) -> s.User:
    username = form_data.username
    password = form_data.password
    exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

    db_user = db.query(m.User).filter(m.User.username == username).first()
    if db_user is None:
        raise exception
    if not Password.verify(password, db_user.password):
        raise exception
    return s.User.from_orm(db_user)


def create_user(user: s.UserCreate, db: Session = Depends(get_db)) -> s.User:
    db_user = db.query(m.User).filter(m.User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is not available")
    user.password = Password.hash(user.password)
    db_user = m.User(**user.dict(exclude={'password2'}))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return s.User.from_orm(db_user)
