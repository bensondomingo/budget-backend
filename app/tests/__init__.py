import pytest

from app.core.database import Base, engine, SessionLocal
from app.auth.models import User as UserModel
from app.budget.models import Budget as BudgetModel
from app.services.utils import get_default_date_range
from app.services.security import Password


@pytest.fixture(scope='module', autouse=True)
def setup_teardown_database():
    """
    Handles creation and cleanup of database
    """
    # Create database tables
    Base.metadata.create_all(engine)

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

    with SessionLocal() as db:
        db.add(admin_user)
        db.add(test_user)
        db.flush()

        budget1 = BudgetModel(
            name='budget-expenses-1', category='exp',
            planned_amount=1000, month=get_default_date_range().start,
            user_id=test_user.id)
        budget2 = BudgetModel(
            name='budget-expenses-2', category='exp',
            planned_amount=2000, month=get_default_date_range().start,
            user_id=test_user.id)
        budget3 = BudgetModel(
            name='budget-expenses-3', category='exp',
            planned_amount=3000, month=get_default_date_range().start,
            user_id=test_user.id)
        budget4 = BudgetModel(
            name='budget-income-1', category='inc', planned_amount=10000,
            month=get_default_date_range().start, user_id=test_user.id)
        budget5 = BudgetModel(
            name='budget-income-2', category='inc', planned_amount=10000,
            month=get_default_date_range().start, user_id=test_user.id)
        db.add_all([budget1, budget2, budget3, budget4, budget5])

        db.add_all([budget1, budget2, budget3, budget4, budget5])
        db.commit()

    yield None
    Base.metadata.drop_all(engine)
