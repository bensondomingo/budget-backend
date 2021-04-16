from fastapi import FastAPI as FA
from fastapi.logger import logger
from aioredis import create_redis_pool, Redis

from .auth.routes import auth_router, user_router
from .budget.routes import budget_router, transactions_router


class FastAPI(FA):
    def __init__(self) -> None:
        super().__init__()
        self.redis: Redis


app = FastAPI()


@app.on_event('startup')
async def on_start():
    logger.info('App init')
    logger.info('Connecting to redis database ... ')
    redis = await create_redis_pool('redis://redis', db=3)
    app.redis = redis


@app.on_event('shutdown')
async def on_shutdown():
    app.redis.close()
    await app.redis.wait_closed()


app.include_router(auth_router)
app.include_router(user_router)
app.include_router(budget_router)
app.include_router(transactions_router)
