from pydantic.types import UUID4  # pylint: disable=no-name-in-module
from fastapi import status
from fastapi.exceptions import HTTPException
from fastapi.param_functions import Depends
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

import app.auth.schemas as us
from app.dependecies import get_async_db, get_current_user
from . import models as m


async def get_budget(
        budget_id: UUID4,
        db: AsyncSession = Depends(get_async_db),
        user: us.User = Depends(get_current_user)) -> m.Budget:
    stmt = select(m.Budget).filter_by(id=budget_id, user_id=user.id)
    result = (await db.execute(stmt)).one_or_none()
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Budget with id {budget_id} not found')
    return result.Budget


async def get_transaction(
        transaction_id: UUID4,
        db: AsyncSession = Depends(get_async_db),
        user: us.User = Depends(get_current_user)):

    stmt = select(m.Transaction).options(selectinload(m.Transaction.budget)).\
        filter_by(id=transaction_id,  user_id=user.id)

    result = (await db.execute(stmt)).scalar_one_or_none()
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return result
