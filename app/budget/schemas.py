# pylint: disable=no-name-in-module
import enum
from datetime import datetime

from pydantic import BaseModel, Field, PositiveFloat, UUID4


class BudgetCategoryEnum(str, enum.Enum):
    inc = 'income'
    ded = 'deductions'
    exp = 'expenses'
    sav = 'savings'


class BudgetBase(BaseModel):
    name: str = Field(...)
    category: BudgetCategoryEnum = Field(
        BudgetCategoryEnum.exp,
        description='income|deductions|expenses|savings',
        regex='^income$|^deductions$|^expenses$|^savings$')
    planned_amount: PositiveFloat = Field(...)


class BudgetCreate(BudgetBase):
    pass


class BudgetUpdate(BudgetBase):
    name: str = Field(None)
    category: BudgetCategoryEnum = Field(
        None, description='income|deductions|expenses|savings',
        regex='^income$|^deductions$|^expenses$|^savings$')
    planned_amount: PositiveFloat = Field(None)


class Budget(BudgetBase):
    id: UUID4 = Field(...)
    user_id: UUID4 = Field(...)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)

    class Config:
        orm_mode = True


class TransactionBase(BaseModel):
    amount: PositiveFloat = Field(...)
    description: str = Field(..., max_length=100)
    date: datetime = Field(datetime.utcnow())


class TransactionCreate(TransactionBase):
    pass


class TransactcionUpdate(TransactionBase):
    amount: PositiveFloat = Field(None)
    description: str = Field(None, max_length=100)
    date: datetime = Field(None)
    budget_id: UUID4 = Field(None)


class Transaction(TransactionBase):
    id: UUID4 = Field(...)
    user_id: UUID4 = Field(...)
    budget_id: UUID4 = Field(...)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)

    class Config:
        orm_mode = True
