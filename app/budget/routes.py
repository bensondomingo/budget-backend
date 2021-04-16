from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.param_functions import Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession
from starlette.status import HTTP_200_OK

from app.auth.schemas import User
from app.dependecies import get_async_db, get_current_user
from . import models as m, schemas as s

from .dep import get_budget

budget_router = APIRouter(prefix='/budgets', tags=['budgets'])
transactions_router = APIRouter(prefix='/transactions', tags=['transactions'])


@budget_router.post(
    '/', response_model=s.Budget,
    status_code=status.HTTP_201_CREATED)
async def add_budget(
        budget: s.BudgetCreate,
        db: AsyncSession = Depends(get_async_db),
        user: User = Depends(get_current_user)):

    stmt = select(m.Budget).where(m.Budget.name == budget.name)
    result = (await db.execute(stmt)).one_or_none()
    if result is not None:
        raise HTTPException(
            status_code=400, detail="Budget name already exists")

    db_budget = m.Budget(**budget.dict(), user_id=user.id)
    db.add(db_budget)
    await db.flush()
    await db.commit()
    await db.refresh(db_budget)
    return db_budget


@budget_router.get(
    '/', response_model=List[s.Budget],
    status_code=status.HTTP_200_OK)
async def read_user_budgets(
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_async_db),
        user: User = Depends(get_current_user),
        category: Optional[List[str]] = Query(
            None, description='income | deductions | expenses | savings',
            regex='^income$|^deductions$|^expenses$|^savings$')):

    stmt = select(m.Budget).where(
        m.Budget.user_id == user.id)
    if category is not None:
        stmt = stmt.where(m.Budget.category.in_(category))

    result = (await db.execute(stmt.offset(skip).limit(limit))).all()
    return [row.Budget for row in result]


@budget_router.get('/{budget_id}', response_model=s.Budget)
async def read_budget(budget: m.Budget = Depends(get_budget)):
    return budget


@budget_router.patch('/{budget_id}', response_model=s.Budget)
async def update_budget(
        budget_schema: s.BudgetUpdate,
        budget_model: m.Budget = Depends(get_budget),
        db: AsyncSession = Depends(get_async_db)):

    if budget_schema.name:
        budget_model.name = budget_schema.name
    if budget_schema.category:
        budget_model.category = budget_schema.category
    if budget_schema.planned_amount:
        budget_model.planned_amount = budget_schema.planned_amount

    db.add(budget_model)
    await db.flush()
    await db.commit()
    await db.refresh(budget_model)
    return budget_model


@budget_router.delete(
    '/{budget_id}',
    status_code=status.HTTP_204_NO_CONTENT)
async def remove_budget(budget: m.Budget = Depends(get_budget),
                        db: AsyncSession = Depends(get_async_db)):

    await db.delete(budget)
    await db.flush()
    await db.commit()


@transactions_router.post(
    '/{budget_id}', status_code=status.HTTP_201_CREATED,
    response_model=s.Transaction)
async def add_transaction(
        transaction: s.TransactionCreate,
        budget_model: m.Budget = Depends(get_budget),
        db: AsyncSession = Depends(get_async_db)):

    db_transaction = m.Transaction(**transaction.dict(),
                                   user_id=budget_model.user_id,
                                   budget_id=budget_model.id)
    db.add(db_transaction)
    await db.flush()
    await db.commit()
    return db_transaction


@transactions_router.get(
    '/', response_model=List[s.Transaction],
    status_code=HTTP_200_OK)
async def read_transactions():
    pass
