# pylint: disable=redefined-outer-name
# pylint: disable=too-many-statements
# pylint: disable=unused-argument
# pylint: disable=unused-import
from uuid import uuid4
from datetime import date

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy.sql.expression import delete, select
from sqlalchemy.sql.functions import func
from starlette.status import HTTP_200_OK

from app.budget.models import (
    Budget as BudgetModel, Transaction as TransactionModel)
from app.budget.schemas import (
    Budget as BudgetSchema, PaginatedTransactions,
    Transaction as TransactionSchema)
from app.core.database import engine, SessionLocal
from app.main import app
from app.services.utils import YearMonth, get_date_range
from . import (get_auth_header__admin_user, get_auth_header__test_user, url)


@pytest.fixture(scope='function',)
def get_budgets():
    stmt = select(BudgetModel)
    this_month = get_date_range().start
    last_month = get_date_range(
        YearMonth(year=this_month.year, month=this_month.month - 1)).start
    with SessionLocal() as session:
        result = session.execute(stmt).scalars().all()
        btm = [BudgetSchema.from_orm(b)
               for b in result if b.month == this_month]
        blm = [BudgetSchema.from_orm(b)
               for b in result if b.month == last_month]
        return {'last_month': blm, 'this_month': btm}


@pytest.fixture(scope='function', autouse=True)
def transaction_create_cleanup():
    yield None
    stmt = delete(TransactionModel).where(~TransactionModel.description.in_(
        ['test-transacation-1', 'test-transacation-2', 'test-transacation-3',
         'test-transacation-4', 'test-transacation-5']))
    with SessionLocal() as db:
        db.execute(stmt)
        db.commit()

        stmt = select(func.count('*')).select_from(TransactionModel)
        result = db.execute(stmt).scalar()
        assert result == 10


class TestListTransactions:

    url = f'{url}/transactions'

    def test_list__all_transactions(self, get_auth_header__test_user):
        with TestClient(app) as client:
            resp = client.get(self.url, headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_200_OK
            # Why length ==10? See setup_teardown_database fixture
            assert len(resp.json().get('items')) == 10

    def test_list__query_params__category(self, get_auth_header__test_user):
        with TestClient(app) as client:
            resp = client.get(self.url,
                              headers=get_auth_header__test_user,
                              params={'category': 'expenses'})
            assert resp.status_code == status.HTTP_200_OK
            assert len(resp.json().get('items')) == 6
            resp = client.get(self.url,
                              headers=get_auth_header__test_user,
                              params={'category': 'income'})
            assert resp.status_code == status.HTTP_200_OK
            assert len(resp.json().get('items')) == 4
            resp = client.get(self.url,
                              headers=get_auth_header__test_user,
                              params={'category': ['income', 'expenses']})
            assert resp.status_code == status.HTTP_200_OK
            assert len(resp.json().get('items')) == 10

    def test_list__query_params__month(self, get_auth_header__test_user):
        with TestClient(app) as client:
            # this month
            date_start = get_date_range().start
            date_end = get_date_range().end
            resp = client.get(self.url, headers=get_auth_header__test_user,
                              params={'start': date_start, 'end': date_end})
            assert resp.status_code == status.HTTP_200_OK
            assert len(resp.json().get('items')) == 5

            # last month
            last_month_range = get_date_range(YearMonth(
                year=date_start.year, month=date_start.month - 1))
            resp = client.get(self.url, headers=get_auth_header__test_user,
                              params={'start': last_month_range.start,
                                      'end': last_month_range.end})
            assert resp.status_code == status.HTTP_200_OK
            assert len(resp.json().get('items')) == 5

            # specific range
            # 15th last month to 15th this month
            start = last_month_range.start.replace(day=15)
            end = date_start.replace(day=15)
            resp = client.get(self.url, headers=get_auth_header__test_user,
                              params={'start': start, 'end': end})
            assert resp.status_code == status.HTTP_200_OK
            transactions = PaginatedTransactions(**resp.json())

            assert transactions.meta.total == 7
            income = [item for item in transactions.items
                      if item.category == 'income']
            expenses = [item for item in transactions.items
                        if item.category == 'expenses']
            assert len(income) == 3
            assert len(expenses) == 4

    def test_list__not_authenticated(self):
        with TestClient(app) as client:
            resp = client.get(self.url)
            assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list__user_no_recoreds(self, get_auth_header__admin_user):
        with TestClient(app) as client:
            resp = client.get(self.url, headers=get_auth_header__admin_user)
            assert resp.status_code == status.HTTP_200_OK
            assert len(resp.json().get('items')) == 0


class TestCreateTransactions:

    url = f'{url}/transactions'

    def test_create__invalid_amount(
            self, get_budgets, get_auth_header__test_user):
        budget = get_budgets.get('this_month')[0]
        with TestClient(app) as client:
            resp = client.post(
                f'{self.url}/{str(budget.id)}',
                json={'amount': -1, 'description': 'expenses-1'},
                headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create__sunny_case(self, get_budgets, get_auth_header__test_user):
        budget = get_budgets.get('this_month')[0]
        with TestClient(app) as client:
            resp = client.post(
                f'{self.url}/{str(budget.id)}',
                json={'amount': 400, 'description': 'expenses-1'},
                headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_201_CREATED

            resp = client.get(self.url, headers=get_auth_header__test_user,
                              params={
                                  'start': str(get_date_range().start),
                                  'end': str(get_date_range().end)})
            assert resp.status_code == status.HTTP_200_OK
            assert len(resp.json().get('items')) == 6  # 5 default, 1 created

    def test_create__budget_not_found(self, get_auth_header__test_user):
        budget_id = uuid4()
        with TestClient(app) as client:
            resp = client.post(
                f'{self.url}/{str(budget_id)}',
                json={'amount': 400, 'description': 'expenses-1'},
                headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_create__no_description(
            self, get_budgets, get_auth_header__test_user):
        budget = get_budgets.get('this_month')[0]
        with TestClient(app) as client:
            resp = client.post(
                f'{self.url}/{str(budget.id)}', json={'amount': 400},
                headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create__invalid_date(
            self, get_budgets, get_auth_header__test_user):
        """
        Transaction date should be within the budget's month range.
        """
        budget: BudgetSchema = get_budgets.get('this_month')[0]
        month = budget.month.month - 1
        year = budget.month.year
        if month < 1:
            month, year = 12, year - 1

        transaction_date = '{}-{:02}-04'.format(year, month)
        with TestClient(app) as client:
            resp = client.post(
                f'{self.url}/{str(budget.id)}',
                json={'amount': 400, 'description': 'expenses-1',
                      'date': transaction_date},
                headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

            budget = get_budgets['last_month'][0]
            resp = client.post(
                f'{self.url}/{str(budget.id)}',
                json={'amount': 400, 'description': 'expenses-1',
                      'date': transaction_date},
                headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_201_CREATED


class TestRetrieveTransaction:

    url = f'{url}/transactions'

    @pytest.fixture(scope='function')
    def get_test_transaction(self, get_auth_header__test_user):
        with TestClient(app) as client:
            resp = client.get(self.url, headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_200_OK
            transactions = PaginatedTransactions(**resp.json())
            return transactions.items[0]

    def test_retrieve__sunny_case(
            self, get_test_transaction, get_auth_header__test_user):
        t1 = get_test_transaction
        with TestClient(app) as client:
            resp = client.get(f'{self.url}/{t1.id}',
                              headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_200_OK
            t2 = TransactionSchema(**resp.json())
            assert t1.id == t2.id
            assert t1.description == t2.description
            assert t1.date == t2.date
            assert t1.user_id == t2.user_id
            assert t1.budget_id == t2.budget_id
            assert t1.category == t2.category
            assert t1.created_at == t2.created_at
            assert t1.updated_at == t2.updated_at

    def test_retrieve__different_user(
            self, get_test_transaction, get_auth_header__admin_user):
        t1 = get_test_transaction
        with TestClient(app) as client:
            resp = client.get(f'{self.url}/{t1.id}',
                              headers=get_auth_header__admin_user)
            assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve__not_authenticated(self, get_test_transaction):
        t1 = get_test_transaction
        with TestClient(app) as client:
            resp = client.get(f'{self.url}/{t1.id}')
            assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestDeleteTransaction:

    url = f'{url}/transactions'

    def test_delete__sunny_case(self, get_budgets, get_auth_header__test_user):
        # 1. Create a new transaction
        budget = get_budgets.get('this_month')[0]
        with TestClient(app) as client:
            resp = client.post(
                f'{self.url}/{str(budget.id)}',
                json={'amount': 1000, 'description': 'expenses-1'},
                headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_201_CREATED
            transaction = TransactionSchema(**resp.json())

            # 2. Count all transactions
            resp = client.get(self.url, headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_200_OK
            assert PaginatedTransactions(**resp.json()).meta.total == 11

            # 3. Delete newly transaction
            resp = client.delete(f'{self.url}/{transaction.id}',
                                 headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_204_NO_CONTENT

            # 4. Recount transactions
            resp = client.get(self.url, headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_200_OK
            assert PaginatedTransactions(**resp.json()).meta.total == 10

    def test_delete__different_user(
            self, get_budgets, get_auth_header__test_user,
            get_auth_header__admin_user):
        # 1. Create a new transaction
        budget = get_budgets.get('this_month')[0]
        with TestClient(app) as client:
            resp = client.post(
                f'{self.url}/{str(budget.id)}',
                json={'amount': 1000, 'description': 'expenses-1'},
                headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_201_CREATED
            transaction = TransactionSchema(**resp.json())

            # 2. Count all transactions
            resp = client.get(self.url, headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_200_OK
            assert PaginatedTransactions(**resp.json()).meta.total == 11

            # 3. Try delete newly transaction, but with different user
            resp = client.delete(f'{self.url}/{transaction.id}',
                                 headers=get_auth_header__admin_user)
            assert resp.status_code == status.HTTP_404_NOT_FOUND

            # 4. Recount transactions
            resp = client.get(self.url, headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_200_OK
            assert PaginatedTransactions(**resp.json()).meta.total == 11

    def test_delete__not_authenticated(
            self, get_budgets, get_auth_header__test_user):
        # 1. Create a new transaction
        budget = get_budgets.get('this_month')[0]
        with TestClient(app) as client:
            resp = client.post(
                f'{self.url}/{str(budget.id)}',
                json={'amount': 1000, 'description': 'expenses-1'},
                headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_201_CREATED
            transaction = TransactionSchema(**resp.json())

            # 2. Try delete newly transaction
            resp = client.delete(f'{self.url}/{transaction.id}')
            assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestUpdateTransaction:

    url = f'{url}/transactions'

    @pytest.fixture(scope='function')
    def create_test_transaction(self, get_budgets, get_auth_header__test_user):
        budget: BudgetSchema = get_budgets.get('this_month')[0]
        with TestClient(app) as client:
            resp = client.post(
                f'{self.url}/{str(budget.id)}',
                json={'amount': 1000, 'description': 'expenses-1'},
                headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_201_CREATED
            t = TransactionSchema(**resp.json())
            assert t.amount == 1000
            assert t.description == 'expenses-1'
            assert t.budget_name == budget.name
            assert t.date == date.today()
            assert t.budget_id == budget.id
            return TransactionSchema(**resp.json())

    def test_update__all_fields(
            self, create_test_transaction,
            get_budgets, get_auth_header__test_user):
        t_id: str = str(create_test_transaction.id)
        budget_income, *_ = [b for b in get_budgets['this_month']
                             if b.category == 'income']

        with TestClient(app) as client:
            # 1. Retrieve
            resp = client.get(f'{self.url}/{t_id}',
                              headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_200_OK
            t1 = TransactionSchema(**resp.json())
            assert t1.amount == 1000
            assert t1.description == 'expenses-1'
            assert t1.date == date.today()
            assert t1.category == 'expenses'
            # 2. Update
            new_date = t1.date.replace(
                day=t1.date.day-1 if t1.date.day > 1 else t1.date.day+1)
            resp = client.patch(
                f'{self.url}/{t_id}',
                headers=get_auth_header__test_user,
                json={'amount': 1500,
                      'description': 'income-1',
                      'date': str(new_date),
                      'budget_id': str(budget_income.id)})
            assert resp.status_code == status.HTTP_200_OK
            # 3. Retrieve
            resp = client.get(f'{self.url}/{t_id}',
                              headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_200_OK
            t1 = TransactionSchema(**resp.json())
            assert t1.amount == 1500
            assert t1.description == 'income-1'
            assert t1.budget_name == budget_income.name
            assert t1.budget_id == budget_income.id
            assert t1.date == new_date
            assert t1.category == budget_income.category

    def test_update__amount(
            self, create_test_transaction, get_auth_header__test_user):
        transaction: TransactionSchema = create_test_transaction
        with TestClient(app) as client:
            # 1. Update
            resp = client.patch(
                f'{self.url}/{transaction.id}',
                headers=get_auth_header__test_user,
                json={'amount': 2000})
            assert resp.status_code == status.HTTP_200_OK
            # 2. Retrieve
            resp = client.get(f'{self.url}/{transaction.id}',
                              headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_200_OK
            t = TransactionSchema(**resp.json())
            # Ensure that only amount field was updated
            assert t.amount == 2000
            assert t.description == transaction.description
            assert t.date == transaction.date
            assert t.budget_id == transaction.budget_id
            assert t.budget_name == transaction.budget_name

    def test_update__description(
            self, create_test_transaction, get_auth_header__test_user):
        transaction: TransactionSchema = create_test_transaction
        with TestClient(app) as client:
            # 1. Update
            resp = client.patch(
                f'{self.url}/{transaction.id}',
                headers=get_auth_header__test_user,
                json={'description': 'expenses-1__updated'})
            assert resp.status_code == status.HTTP_200_OK
            # 2. Retrieve
            resp = client.get(f'{self.url}/{transaction.id}',
                              headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_200_OK
            t = TransactionSchema(**resp.json())
            # Ensure that only description field was updated
            assert t.amount == transaction.amount
            assert t.description == 'expenses-1__updated'
            assert t.date == transaction.date
            assert t.budget_id == transaction.budget_id
            assert t.budget_name == transaction.budget_name

    def test_update__date(
            self, create_test_transaction, get_auth_header__test_user):
        t1: TransactionSchema = create_test_transaction
        new_date = t1.date.replace(
            day=t1.date.day-1 if t1.date.day > 1 else t1.date.day+1)
        with TestClient(app) as client:
            # 1. Update
            resp = client.patch(
                f'{self.url}/{t1.id}',
                headers=get_auth_header__test_user,
                json={'date': str(new_date)})
            assert resp.status_code == status.HTTP_200_OK
            # 2. Retrieve
            resp = client.get(f'{self.url}/{t1.id}',
                              headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_200_OK
            t = TransactionSchema(**resp.json())
            # Ensure only date field got updated
            assert t.amount == t1.amount
            assert t.description == t1.description
            assert t.date == new_date
            assert t.category == t1.category
            assert t.budget_id == t1.budget_id
            assert t.budget_name == t1.budget_name

    def test_update__budget_id(
            self, get_budgets, create_test_transaction,
            get_auth_header__test_user):
        t1: TransactionSchema = create_test_transaction
        budget_income, *_ = [b for b in get_budgets['this_month']
                             if b.category == 'income']
        with TestClient(app) as client:
            # 1. Update
            resp = client.patch(
                f'{self.url}/{t1.id}',
                headers=get_auth_header__test_user,
                json={'budget_id': str(budget_income.id)})
            assert resp.status_code == status.HTTP_200_OK
            # 2. Retrieve
            resp = client.get(f'{self.url}/{t1.id}',
                              headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_200_OK
            t = TransactionSchema(**resp.json())
            # Ensure budget related fields got updated
            assert t.amount == t1.amount
            assert t.description == t1.description
            assert t.date == t1.date
            assert t.category == budget_income.category
            assert t.budget_id == budget_income.id
            assert t.budget_name == budget_income.name

    def test_update__budget_id__not_matching_date(
            self, get_budgets, create_test_transaction,
            get_auth_header__test_user):
        t1: TransactionSchema = create_test_transaction
        budget_income, *_ = [b for b in get_budgets['last_month']
                             if b.category == 'income']
        with TestClient(app) as client:
            # 1. Update
            resp = client.patch(
                f'{self.url}/{t1.id}',
                headers=get_auth_header__test_user,
                json={'budget_id': str(budget_income.id)})
            assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

            # 2. Retrive
            resp = client.get(f'{self.url}/{t1.id}',
                              headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_200_OK
            t = TransactionSchema(**resp.json())
            # Ensure nothing got updated
            assert t.amount == t1.amount
            assert t.description == t1.description
            assert t.date == t1.date
            assert t.category == t1.category
            assert t.budget_id == t1.budget_id
            assert t.budget_name == t1.budget_name
            assert t == t1

    def test_update__invalid_amount(
            self, create_test_transaction, get_auth_header__test_user):
        transaction: TransactionSchema = create_test_transaction
        with TestClient(app) as client:
            # 1. Update
            resp = client.patch(
                f'{self.url}/{transaction.id}',
                headers=get_auth_header__test_user,
                json={'amount': 0})
            assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            # 2. Retrieve
            resp = client.get(f'{self.url}/{transaction.id}',
                              headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_200_OK
            t = TransactionSchema(**resp.json())
            # Ensure that only amount field was updated
            assert t.amount == transaction.amount
            assert t.description == transaction.description
            assert t.date == transaction.date
            assert t.budget_id == transaction.budget_id
            assert t.budget_name == transaction.budget_name
            assert t.category == transaction.category

    def test_update__invalid_date(
            self, create_test_transaction, get_auth_header__test_user):
        t1: TransactionSchema = create_test_transaction
        new_date = t1.date.replace(year=t1.date.year-1)
        with TestClient(app) as client:
            # 1. Update
            resp = client.patch(
                f'{self.url}/{t1.id}',
                headers=get_auth_header__test_user,
                json={'date': str(new_date)})
            assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            # 2. Retrieve
            resp = client.get(f'{self.url}/{t1.id}',
                              headers=get_auth_header__test_user)
            assert resp.status_code == status.HTTP_200_OK
            t = TransactionSchema(**resp.json())
            # Ensure only date field got updated
            assert t.amount == t1.amount
            assert t.description == t1.description
            assert t.date == t1.date
            assert t.category == t1.category
            assert t.budget_id == t1.budget_id
            assert t.budget_name == t1.budget_name
            assert t == t1
