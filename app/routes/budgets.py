from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.schemas import Budget, BudgetCreate
from app.database import crud as c
from app.database import schemas as s, models as m
from app.dependecies import get_current_user, get_db

router = APIRouter(tags=['budgets'])


@router.post('/budgets/', response_model=Budget)
def create_budget(
        budget: BudgetCreate,
        db: Session = Depends(get_db),
        user: s.User = Depends(get_current_user)):

    db_budget = db.query(m.Budget).filter(m.Budget.name == budget.name).first()
    if db_budget:
        raise HTTPException(
            status_code=400, detail="Budget name already exists")
    db_budget = m.Budget(**budget.dict(), user_id=user.id)
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return s.Budget.from_orm(db_budget)


@router.get('/budgets/', response_model=List[Budget])
def read_user_budgets(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        user: s.User = Depends(get_current_user)):

    budgets = c.get_budgets(db=db, skip=skip, limit=limit)
    return budgets
