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
