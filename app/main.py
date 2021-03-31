from app.database.models import Budget
from fastapi import FastAPI

from .routes import auth, users, budgets


app = FastAPI()


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(budgets.router)
