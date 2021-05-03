# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
from uuid import uuid4
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy.sql.expression import delete, select
from sqlalchemy.sql.functions import func

from app.main import app
from app.budget.models import Budget as BudgetModel
from app.config import settings
from app.core.database import SessionLocal
from app.services.utils import get_default_date_range, YearMonth
from . import setup_teardown_database  # pylint: disable=unused-import

client = TestClient(app)
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
    Authenticate test user and return Authorization header
    """
    with TestClient(app) as c:
        resp = c.post(signin_url, data={
            'username': 'admin',
            'password': 'password'})
        assert resp.status_code == status.HTTP_200_OK
        token = resp.json().get('access_token')
        return {'Authorization': f'Bearer {token}'}


@pytest.fixture(scope='function')
def budget_create_cleanup():
    yield None
    stmt = delete(BudgetModel).where(~BudgetModel.name.in_(
        ['budget-expenses-1', 'budget-expenses-2', 'budget-expenses-3',
         'budget-income-1', 'budget-income-2']))
    with SessionLocal() as db:
        db.execute(stmt)
        db.commit()

        stmt = select(func.count('*')).select_from(BudgetModel)
        result = db.execute(stmt).scalar()
        assert result == 5


class TestListBudgets:

    url = f'{url}/budgets'

    def test_list__user_authenticated(self, get_auth_header__test_user):
        with TestClient(app) as c:
            resp = c.get(self.url, headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_200_OK
            # Why length == 5? See setup_teardown_database fixture
            assert len(resp.json().get('items')) == 5

    def test_list__user_not_authenticated(self):
        with TestClient(app) as c:
            resp = c.get(self.url)
            assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list__query_params_category(self, get_auth_header__test_user):
        with TestClient(app) as c:
            # read all expenses budgets
            resp = c.get(self.url, headers=get_auth_header__test_user,
                         params={'category': 'expenses'})
            assert resp.status_code == status.HTTP_200_OK
            # Why length == 3? See setup_teardown_database fixture
            assert len(resp.json().get('items')) == 3

            # read all income budgets
            resp = c.get(self.url, headers=get_auth_header__test_user,
                         params={'category': 'income'})
            assert resp.status_code == status.HTTP_200_OK
            # Why length == 2? See setup_teardown_database fixture
            assert len(resp.json().get('items')) == 2

    def test_list__query_params_month(
            self, get_auth_header__test_user, budget_create_cleanup):
        with TestClient(app) as c:
            # Get first day last month
            this_month = get_default_date_range().start
            if this_month.month == 1:
                last_month = get_default_date_range(
                    YearMonth(year=this_month.year - 1))
            else:
                last_month = get_default_date_range(
                    YearMonth(month=this_month.month - 1))
            # Create new budget for last month
            resp = c.post(self.url, headers=get_auth_header__test_user, json={
                'name': 'test-expenses-1',
                'category': 'expenses',
                'planned_amount': 1000,
                'month': str(last_month.start)})
            assert resp.status_code == status.HTTP_201_CREATED
            # Get all budgets from all dates
            resp = c.get(self.url, headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_200_OK
            assert len(resp.json().get('items')) == 6
            # Get all budgets from last month
            resp = c.get(self.url, headers=get_auth_header__test_user,
                         params={'month': str(last_month.start)})
            assert resp.status_code == status.HTTP_200_OK
            assert len(resp.json().get('items')) == 1
            item, *_ = resp.json().get('items')
            assert item['name'] == 'test-expenses-1'

    def test_list__user_no_budget_in_db(self, get_auth_header__admin_user):
        """
        Ensure users can only read budgets that they created.
        """
        with TestClient(app) as c:
            resp = c.get(self.url, headers=get_auth_header__admin_user)
            assert resp.status_code == status.HTTP_200_OK
            # admin user has no budgets created
            assert len(resp.json().get('items')) == 0


class TestCreateBudgets:

    url = f'{url}/budgets'

    def test_create__user_authenticated(
            self, get_auth_header__test_user, budget_create_cleanup):
        with TestClient(app) as c:
            resp = c.post(self.url, headers=get_auth_header__test_user, json={
                'name': 'test-expenses-1',
                'planned_amount': 1000
            })
            assert resp.status_code == status.HTTP_201_CREATED

            data = resp.json()
            assert data['name'] == 'test-expenses-1'
            assert data['category'] == 'expenses'
            assert data['planned_amount'] == 1000
            assert data['month'] == str(get_default_date_range().start)

            token = get_auth_header__test_user.get(
                'Authorization').replace('Bearer ', '')
            payload = jwt.decode(
                token, settings.SECRET_KEY, settings.SECRET_ALGORITHM)
            user_id: str = payload.get('uid')

            assert data.get('id') is not None
            assert data.get('user_id') == user_id

    def test_create__invalid_input(self, get_auth_header__test_user):
        with TestClient(app) as c:
            resp = c.post(self.url, headers=get_auth_header__test_user, json={
                'category': 'expenses',
                'planned_amount': 1000,
                'month': str(get_default_date_range().start)
            })
            assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

            resp = c.post(self.url, headers=get_auth_header__test_user, json={
                'name': 'test-expenses-1',
                'category': 'expenses',
                'month': str(get_default_date_range().start)
            })
            assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestRetrieveBudget:

    url = f'{url}/budgets'

    def test_retrieve__existing_budget(self, get_auth_header__test_user):
        with TestClient(app) as c:
            resp = c.get(self.url, headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_200_OK
            items = resp.json().get('items')
            assert len(items) == 5
            budget, *_ = items
            assert budget.get('id') is not None

            resp = c.get(f"{self.url}/{budget['id']}",
                         headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_200_OK
            assert resp.json() == budget

    def test_retrieve__not_found_budget(self, get_auth_header__test_user):
        with TestClient(app) as c:
            budget_id = uuid4()  # dummy id
            resp = c.get(f"{self.url}/{str(budget_id)}",
                         headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteBudget:

    url = f'{url}/budgets'

    def test_delete__budget_owned_by_user(
            self, get_auth_header__test_user, budget_create_cleanup):
        with TestClient(app) as c:
            resp = c.post(self.url, headers=get_auth_header__test_user, json={
                'name': 'test-expenses-1', 'planned_amount': 1000})
            assert resp.status_code == status.HTTP_201_CREATED
            budget = resp.json()

            resp = c.delete(f"{self.url}/{budget['id']}",
                            headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_204_NO_CONTENT

            resp = c.get(f"{self.url}/{budget['id']}",
                         headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_404_NOT_FOUND
