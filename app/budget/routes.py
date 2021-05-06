import asyncio
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.param_functions import Query
from sqlalchemy import select
from sqlalchemy import func
from sqlalchemy.engine.row import Row
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import update
from starlette.requests import Request
from starlette.status import HTTP_200_OK

from app.auth import schemas as us
from app.config import settings
from app.dependecies import get_async_db, get_current_user
from app.services.utils import (
    generate_page_meta, get_default_date_range, populate_transaction_schema)
from . import models as m, schemas as s
from .dep import get_budget, get_transaction

budget_router = APIRouter(prefix='/budgets', tags=['budgets'])
transactions_router = APIRouter(prefix='/transactions', tags=['transactions'])


@budget_router.get(
    '', response_model=s.PaginatedBudgets,
    status_code=status.HTTP_200_OK)
async def read_user_budgets(
        request: Request,
        offset: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_async_db),
        user: us.User = Depends(get_current_user),
        month: date = Query(None, description='YYYY-MM-01'),
        category: Optional[List[str]] = Query(
            None, description='income | deductions | expenses | savings',
            regex='^income$|^deductions$|^expenses$|^savings$')):

    stmt = select(m.Budget).filter_by(user_id=user.id)
    if month is not None:
        stmt = stmt.where(m.Budget.month == month)
    if category is not None:
        stmt = stmt.where(m.Budget.category.in_(category))
    subq = aliased(m.Budget, stmt.subquery())

    resp = await asyncio.gather(
        db.execute(stmt.offset(offset).limit(limit)),
        db.execute(func.count(subq.id)))
    result, row_count = resp
    paginated_resp = s.PaginatedBudgets(
        meta=generate_page_meta(request, row_count.scalar()),
        items=result.scalars().all())
    return paginated_resp


@budget_router.post(
    '', response_model=s.Budget,
    status_code=status.HTTP_201_CREATED)
async def add_budget(
        budget: s.BudgetCreate,
        db: AsyncSession = Depends(get_async_db),
        user: us.User = Depends(get_current_user)):

    stmt = select(m.Budget).filter_by(name=budget.name, month=budget.month)
    result = (await db.execute(stmt)).one_or_none()
    if result is not None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Budget name already exists")

    db_budget = m.Budget(**budget.dict(), user_id=user.id)
    db.add(db_budget)
    await db.commit()
    return db_budget


@budget_router.get('/{budget_id}', response_model=s.Budget)
async def read_budget(budget: m.Budget = Depends(get_budget)):
    return budget


@budget_router.patch('/{budget_id}', response_model=s.Budget)
async def update_budget(
        budget_schema: s.BudgetUpdate,
        budget_model: m.Budget = Depends(get_budget),
        db: AsyncSession = Depends(get_async_db)):

    update_data = budget_schema.dict(exclude_unset=True)
    stmt = update(m.Budget).where(
        m.Budget.id == budget_model.id).values(**update_data)

    await db.execute(stmt)
    await db.commit()
    return budget_model


@budget_router.delete(
    '/{budget_id}',
    status_code=status.HTTP_204_NO_CONTENT)
async def remove_budget(budget: m.Budget = Depends(get_budget),
                        db: AsyncSession = Depends(get_async_db)):
    await db.delete(budget)
    await db.commit()


@transactions_router.get(
    '', response_model=s.PaginatedTransactions,
    status_code=HTTP_200_OK)
async def read_transactions(
        request: Request,
        offset: int = settings.PAGE_OFFSET,
        limit: int = settings.PAGE_LIMIT,
        start: date = Query(get_default_date_range().start),
        end: date = Query(get_default_date_range().end),
        category: str = Query(None),
        user: us.User = Depends(get_current_user),
        db: AsyncSession = Depends(get_async_db)):

    stmt = select(
        m.Transaction,
        m.Budget.category,
        m.Budget.name.label('budget')).\
        join(m.Budget)
    if category:
        stmt = stmt.where(m.Budget.category == category)
    stmt = stmt.where(m.Transaction.user_id == user.id).\
        where(m.Transaction.date.between(start, end)).\
        order_by(m.Transaction.date)
    subq = aliased(m.Transaction, stmt.subquery())

    transactions, row_count = await asyncio.gather(
        db.execute(stmt.offset(offset).limit(limit)),
        db.execute(select(func.count(subq.id)))
    )

    paginated_resp = s.PaginatedTransactions(
        meta=generate_page_meta(request, row_count.scalar()),
        items=populate_transaction_schema(transactions, s.Transaction))

    return paginated_resp


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
    await db.commit()
    response = s.Transaction.from_orm(db_transaction)
    response.category = budget_model.category
    response.budget = budget_model.name
    return response


@transactions_router.get(
    '/{transaction_id}',
    status_code=status.HTTP_200_OK,
    response_model=s.Transaction)
async def read_transaction(transaction: Row = Depends(get_transaction)):
    t = s.Transaction.from_orm(transaction.Transaction)
    t.category = transaction.category.value
    t.budget = transaction.budget
    return t


@transactions_router.delete(
    '/{transaction_id}',
    status_code=status.HTTP_204_NO_CONTENT)
async def remove_transaction(
        transaction: Row = Depends(get_transaction),
        db: AsyncSession = Depends(get_async_db)):
    await db.delete(transaction.Transaction)
    await db.commit()
