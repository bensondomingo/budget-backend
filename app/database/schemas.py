# pylint: disable=no-name-in-module
import enum
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr, Field, PositiveFloat, UUID4, validator, AnyUrl


class BudgetCategoryEnum(str, enum.Enum):
    inc = 'income'
    ded = 'deductions'
    exp = 'expenses'
    sav = 'savings'


class BudgetBase(BaseModel):
    name: str = Field(...)
    category: BudgetCategoryEnum = Field(
        ..., description='income | expenses | savings')
    planned_amount: PositiveFloat = Field(...)


class BudgetCreate(BudgetBase):
    pass


class Budget(BudgetBase):
    id: UUID4 = Field(...)
    user_id: UUID4 = Field(...)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)

    class Config:
        orm_mode = True


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
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Passwords didn\'t matched')
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
