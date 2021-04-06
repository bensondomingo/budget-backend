from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.param_functions import Query
from pydantic.types import UUID4  # pylint: disable=no-name-in-module
from sqlalchemy.orm import Session

from app.auth.schemas import User
from app.dependecies import get_current_user, get_db
from . import models as m, schemas as s

router = APIRouter(prefix='/budgets', tags=['budgets'])


@router.post('/', response_model=s.Budget, status_code=status.HTTP_201_CREATED)
def add_budget(
        budget: s.BudgetCreate,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user)):

    db_budget = db.query(m.Budget).filter(m.Budget.name == budget.name).first()
    if db_budget:
        raise HTTPException(
            status_code=400, detail="Budget name already exists")
    db_budget = m.Budget(**budget.dict(), user_id=user.id)
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget


@router.get('/', response_model=List[s.Budget], status_code=status.HTTP_200_OK)
def read_user_budgets(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
        category: Optional[List[str]] = Query(
            None, description='income | deductions | expenses | savings')):

    q = db.query(m.Budget).filter_by(user_id=user.id)
    if category is not None:
        q = q.filter(m.Budget.category.in_(category))

    return q.offset(skip).limit(limit).all()


@router.get('/{budget_id}', response_model=s.Budget)
def read_budget(budget_id: UUID4, user: User = Depends(
        get_current_user), db: Session = Depends(get_db)):

    db_budget = db.query(m.Budget).filter_by(
        user_id=user.id, id=budget_id).first()
    if db_budget is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return db_budget
