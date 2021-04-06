""" Project level dependencies lives here """
from typing import Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import jwt, JWTError


from app import banned_token_registry
from .config import settings
from .core.database import AsyncSessionLocal, SessionLocal
from .auth import models as um, schemas as us
from .errors import credentials_exception
from .services.security import oauth2_scheme, Password


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


def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)) -> us.User:

    # Ensure that token is not banned, else raise credential_exception
    if banned_token_registry.exists(token):
        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.SECRET_KEY,
                             settings.SECRET_ALGORITHM)
        username: Union[str, None] = payload.get('sub')
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    db_user = db.query(um.User).filter(
        um.User.username == username).first()
    if db_user is None:
        raise credentials_exception
    return us.User.from_orm(db_user)


async def async_get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_async_db)) -> us.User:

    # Ensure that token is not banned, else raise credential_exception
    if banned_token_registry.exists(token):
        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.SECRET_KEY,
                             settings.SECRET_ALGORITHM)
        username: Union[str, None] = payload.get('sub')
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    stmt = select(um.User).where(um.User.username == username)
    result = (await db.execute(stmt)).fetchone()
    return result.User


def get_admin_user(user: us.User = Depends(get_current_user)) -> us.User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user


def authenticate_user(
        db: Session = Depends(get_db),
        form_data: OAuth2PasswordRequestForm = Depends()) -> us.User:
    username = form_data.username
    password = form_data.password
    exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

    db_user = db.query(um.User).filter(
        um.User.username == username).first()
    if db_user is None:
        raise exception
    if not Password.verify(password, db_user.password):
        raise exception
    return us.User.from_orm(db_user)


def create_user(user: us.UserCreate, db: Session = Depends(get_db)) -> us.User:
    db_user = db.query(um.User).filter(
        um.User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is in use")
    user.password = Password.hash(user.password)
    db_user = um.User(**user.dict(exclude={'password2'}))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return us.User.from_orm(db_user)
