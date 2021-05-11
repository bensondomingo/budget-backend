# pylint: disable=too-many-locals
from datetime import date

import pytest

from app.auth.models import User as UserModel
from app.budget.models import (
    Budget as BudgetModel, Transaction as TransactionModel)
from app.core.database import Base, engine, SessionLocal
from app.services.security import Password
from app.services.utils import get_date_range, YearMonth


@pytest.fixture(scope='session', autouse=True)
def setup_teardown_database():
    """
    Handles creation and cleanup of database
    """
    # Create database tables
    Base.metadata.create_all(engine)

    with SessionLocal() as db:

        # Create test users
        admin_user = UserModel()
        admin_user.username = 'admin'
        admin_user.email = 'admin@example.com'
        admin_user.password = Password.hash('password')
        admin_user.is_admin = True

        test_user = UserModel()
        test_user.username = 'test'
        test_user.email = 'test@example.com'
        test_user.password = Password.hash('password')
        db.add_all([admin_user, test_user])
        db.flush()

        # Create test budgets
        today = date.today()
        this_month = get_date_range(
            YearMonth(year=today.year, month=today.month)).start
        last_month = this_month.replace(month=this_month.month - 1)
        # 1. budgets from last month. Three expenses, two incomes
        budget1 = BudgetModel(
            name='budget-expenses-1', category='exp', planned_amount=1000,
            month=last_month, user_id=test_user.id)
        budget2 = BudgetModel(
            name='budget-expenses-2', category='exp', planned_amount=1000,
            month=last_month, user_id=test_user.id)
        budget3 = BudgetModel(
            name='budget-expenses-3', category='exp', planned_amount=1000,
            month=last_month, user_id=test_user.id)
        budget4 = BudgetModel(
            name='budget-income-1', category='inc', planned_amount=10000,
            month=last_month, user_id=test_user.id)
        budget5 = BudgetModel(
            name='budget-income-2', category='inc', planned_amount=20000,
            month=last_month, user_id=test_user.id)
        # 2. budgets for this month, Three expenses, two incomes
        budget6 = BudgetModel(
            name='budget-expenses-1', category='exp', planned_amount=1000,
            month=this_month, user_id=test_user.id)
        budget7 = BudgetModel(
            name='budget-expenses-2', category='exp', planned_amount=2000,
            month=this_month, user_id=test_user.id)
        budget8 = BudgetModel(
            name='budget-expenses-3', category='exp', planned_amount=3000,
            month=this_month, user_id=test_user.id)
        budget9 = BudgetModel(
            name='budget-income-1', category='inc', planned_amount=10000,
            month=this_month, user_id=test_user.id)
        budget10 = BudgetModel(
            name='budget-income-2', category='inc', planned_amount=10000,
            month=this_month, user_id=test_user.id)
        db.add_all([budget1, budget2, budget3, budget4, budget5,
                   budget6, budget7, budget8, budget9, budget10])
        db.flush()

        # Create test transactions
        # 1. transactions last month. Three expenses, two incomes
        transaction_1 = TransactionModel(
            amount=100, description='test-transacation-1',
            user_id=test_user.id, budget_id=budget1.id,
            date=last_month.replace(day=1))
        transaction_2 = TransactionModel(
            amount=200, description='test-transacation-2',
            user_id=test_user.id, budget_id=budget2.id,
            date=last_month.replace(day=8))
        transaction_3 = TransactionModel(
            amount=300, description='test-transacation-3',
            user_id=test_user.id, budget_id=budget3.id,
            date=last_month.replace(day=15))
        transaction_4 = TransactionModel(
            amount=5000, description='test-transacation-4',
            user_id=test_user.id, budget_id=budget4.id,
            date=last_month.replace(day=15))
        transaction_5 = TransactionModel(
            amount=6000, description='test-transacation-5',
            user_id=test_user.id, budget_id=budget5.id,
            date=last_month.replace(day=30))
        # 2. transaction for this month. Three expenses, two incomes
        transaction_6 = TransactionModel(
            amount=100, description='test-transacation-1',
            user_id=test_user.id, budget_id=budget6.id,
            date=this_month.replace(day=1))
        transaction_7 = TransactionModel(
            amount=100, description='test-transacation-2',
            user_id=test_user.id, budget_id=budget7.id,
            date=this_month.replace(day=8))
        transaction_8 = TransactionModel(
            amount=100, description='test-transacation-3',
            user_id=test_user.id, budget_id=budget8.id,
            date=this_month.replace(day=15))
        transaction_9 = TransactionModel(
            amount=5000, description='test-transacation-4',
            user_id=test_user.id, budget_id=budget9.id,
            date=this_month.replace(day=15))
        transaction_10 = TransactionModel(
            amount=6000, description='test-transacation-5',
            user_id=test_user.id, budget_id=budget10.id,
            date=this_month.replace(day=30))

        db.add_all([transaction_1, transaction_2, transaction_3, transaction_4,
                    transaction_5, transaction_6, transaction_7, transaction_8,
                    transaction_9, transaction_10])

        db.commit()

    yield None
    Base.metadata.drop_all(engine)
