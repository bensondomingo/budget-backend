from datetime import date

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.sql.expression import select

from app.config import settings
from app.core.database import Base, engine, SessionLocal
from app.auth.models import User as UserModel
from app.budget.models import (
    Budget as BudgetModel, Transaction as TransactionModel)
from app.main import app
from app.services.security import Password, Payload, create_access_token
from app.services.utils import get_date_range, YearMonth


url = f'http://{settings.SERVER_HOST}:{settings.SERVER_PORT}'
signin_url = f'{url}/auth/signin'


@pytest.fixture(scope='function')
def get_auth_header__test_user():
    """
    Authenticate test user and return Authorization header
    """
    with TestClient(app) as c:
        resp = c.post(signin_url, data={
            'username': 'test',
            'password': 'password'})
        assert resp.status_code == status.HTTP_200_OK
        token = resp.json().get('access_token')
        return {'Authorization': f'Bearer {token}'}


@pytest.fixture(scope='function')
def get_auth_header__admin_user():
    """
    Authenticate admin user and return Authorization header
    """
    with TestClient(app) as c:
        resp = c.post(signin_url, data={
            'username': 'admin',
            'password': 'password'})
        assert resp.status_code == status.HTTP_200_OK
        token = resp.json().get('access_token')
        return {'Authorization': f'Bearer {token}'}


@pytest.fixture(scope='function')
def geth_auth_header():
    """
    Manually generate an authentication header for test user
    """
    stmt = select(UserModel).filter_by(username='test')
    with SessionLocal() as session:
        result = session.execute(stmt).one()
        user: UserModel = result.User
        payload = Payload(uid=str(user.id), sub=user.username)
        token = create_access_token(payload)
        return {'Authorization': f'Bearer {token}'}
