from typing import List, Optional
from fastapi import HTTPException, status
from pydantic import BaseModel, validator


class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True


class BudgetBase(BaseModel):
    name: str
    category: str
    planned_amount: float


class BudgetCreate(BudgetBase):
    pass


class Budget(BudgetBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str
    password2: str

    @validator('password2')
    @classmethod
    def passwords_must_match(cls, v: str, values: dict):
        if v != values.get('password'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Passwords are not match')
        return v


class User(UserBase):
    id: int
    is_active: bool = True
    is_admin: bool = False
    budgets: List[Budget] = []

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class BanToken(BaseModel):
    access_token: str
    reason: str
