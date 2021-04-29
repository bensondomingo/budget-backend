# pylint: disable=no-name-in-module
from datetime import datetime

from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr, Field, UUID4, validator


class UserBase(BaseModel):
    username: str = Field(..., max_length=100)
    email: EmailStr = Field(...)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    password2: str = Field(..., min_length=8)

    @validator('password2')
    @classmethod
    def passwords_must_match(cls, v: str, values: dict):
        if v != values.get('password'):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="passwords don't match")
        return v


class UserChangePassword(BaseModel):
    password: str = Field(..., min_length=8)
    password2: str = Field(..., min_length=8)

    @validator('password2')
    @classmethod
    def passwords_must_match(cls, v: str, values: dict):
        if v != values.get('password'):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="passwords don't match")
        return v


class User(UserBase):
    id: UUID4 = Field(...)
    is_active: bool = Field(True)
    is_admin: bool = Field(False)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class BanToken(BaseModel):
    access_token: str
    reason: str
