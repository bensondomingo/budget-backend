import enum
from typing import List, TypeVar
from datetime import date as Date, datetime

from pydantic import BaseModel, Field, PositiveFloat, UUID4  # pylint: disable=no-name-in-module

from app.services.utils import get_date_range, PageMeta

T = TypeVar('T')


class BudgetCategoryEnum(str, enum.Enum):
    inc = 'income'
    exp = 'expenses'


class BudgetBase(BaseModel):
    name: str = Field(...)
    category: BudgetCategoryEnum = Field(
        BudgetCategoryEnum.exp,
        description='|'.join([k.value for k in BudgetCategoryEnum]),
        regex='|'.join([f'^{k.value}$' for k in BudgetCategoryEnum]))
    description: str = Field(None)
    examples: List[str] = Field(
        None, description='List of possible transactions')
    planned_amount: float = Field(..., ge=0)
    month: Date = Field(get_date_range().start)


class BudgetCreate(BudgetBase):
    pass


class BudgetUpdate(BudgetBase):
    name: str = Field(None)
    category: BudgetCategoryEnum = Field(
        None, description='|'.join([k.value for k in BudgetCategoryEnum]),
        regex='|'.join([f'^{k.value}$' for k in BudgetCategoryEnum]))
    planned_amount: float = Field(None, ge=0)
    month: Date = Field(None)


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
    date: Date = Field(Date.today())


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    amount: PositiveFloat = Field(None)
    description: str = Field(None, max_length=100)
    date: Date = Field(None)
    budget_id: UUID4 = Field(None)


class TransactcionUpdate(TransactionBase):
    amount: PositiveFloat = Field(None)
    description: str = Field(None, max_length=100)
    date: Date = Field(None)
    budget_id: UUID4 = Field(None)


class Transaction(TransactionBase):
    id: UUID4 = Field(...)
    user_id: UUID4 = Field(...)
    budget_id: UUID4 = Field(...)
    budget_name: str = Field(None)
    category: str = Field(None)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)

    class Config:
        orm_mode = True


class Pagination(BaseModel):
    meta: PageMeta
    items: List[T]


class PaginatedBudgets(Pagination):
    items: List[Budget]


class PaginatedTransactions(Pagination):
    items: List[Transaction]
