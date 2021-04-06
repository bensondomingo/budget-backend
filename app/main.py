from fastapi import FastAPI

from .auth.routes import auth_router, user_router
from .budget.routes import router as budget_router


app = FastAPI()


app.include_router(auth_router)
app.include_router(user_router)
app.include_router(budget_router)
