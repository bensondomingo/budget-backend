import uuid
from datetime import date

from sqlalchemy import (Column, Date, Enum, Float, ForeignKey, func,
                        String, TIMESTAMP, UniqueConstraint)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.services.utils import get_date_range
from .schemas import BudgetCategoryEnum, BudgetCreate


class Budget(Base):
    """ Docs later """
    __tablename__ = 'budget'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), index=True, nullable=False)
    category = Column(Enum(BudgetCategoryEnum), index=True, nullable=False)
    description = Column(String(200))
    examples = Column(ARRAY(String))
    planned_amount = Column(Float, nullable=False)
    month = Column(Date, default=get_date_range().start)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True),
                        server_default=func.now(), onupdate=func.now())

    # Foreign Keys
    user_id = Column(UUID(as_uuid=True), ForeignKey('user.id'))

    # Relationships
    transactions = relationship('Transaction', backref='budget')

    __mapper_args__ = {"eager_defaults": True}
    __table_args__ = (UniqueConstraint('name', 'month'),)


class Transaction(Base):
    """ Docs later """
    __tablename__ = 'transaction'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(Date, default=date.today())
    amount = Column(Float, nullable=False)
    description = Column(String(100), nullable=False)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True),
                        server_default=func.now(), onupdate=func.now())

    # Foreign Keys
    user_id = Column(UUID(as_uuid=True), ForeignKey('user.id'))
    budget_id = Column(UUID(as_uuid=True),
                       ForeignKey('budget.id'), nullable=True)

    __mapper_args__ = {"eager_defaults": True}


default_budgets = [
    BudgetCreate(
        name='utilities', category='expenses', planned_amount=0,
        examples=['electricity and gas', 'water',
                  'internet and phone', 'cable or satellite'],
        month=get_date_range().start
    ),
    BudgetCreate(
        name='housing', category='expenses', planned_amount=0,
        examples=['rent', 'mortgage', 'repairs', 'insurance'],
        month=get_date_range().start
    ),
    BudgetCreate(
        name='food', category='expenses', planned_amount=0,
        examples=['groceries', 'wet market', 'eating out'],
        month=get_date_range().start
    ),
    BudgetCreate(
        name='transaportation', category='expenses', planned_amount=0,
        examples=['fare', 'car payment', 'auto insurance',
                  'fuel', 'repair', 'toll gate'],
        month=get_date_range().start
    ),
    BudgetCreate(
        name='insurance', category='expenses', planned_amount=0,
        examples=['health', 'dental', 'vision', 'prescriptions',
                  'life and disability', 'out-of-pocket fees'],
        month=get_date_range().start
    ),
    BudgetCreate(
        name='debt', category='expenses', planned_amount=0,
        examples=['house loan', 'car loan', 'credit cards', 'personal loans'],
        month=get_date_range().start
    ),
    BudgetCreate(
        name='leisure', category='expenses', planned_amount=0,
        examples=['vacations', 'trips', 'subscriptions',
                  'gifts', 'movies', 'entertainments'],
        month=get_date_range().start
    ),
    BudgetCreate(
        name='education', category='expenses', planned_amount=0,
        examples=['tuition fees', 'books', 'children allowance',
                  'school supplies', 'extracurricular', 'online courses'],
        month=get_date_range().start
    ),
    BudgetCreate(
        name='personal', category='expenses', planned_amount=0,
        examples=['toiletries', 'shoes', 'bags', 'fashion',
                  'beauty', 'barber shop', 'clothing', 'laundry'],
        month=get_date_range().start
    ),
    BudgetCreate(
        name='miscellaneous', category='expenses', planned_amount=0,
        examples=['child care', "kid's allowance", 'pet care'],
        month=get_date_range().start
    ),
    BudgetCreate(
        name='benevolence', category='expenses', planned_amount=0,
        examples=['charity', 'church offerings', 'tithes', 'helping others'],
        month=get_date_range().start
    ),
    BudgetCreate(
        name='deductions', category='expenses', planned_amount=0,
        description='deductions from salary',
        examples=['tax', 'other mandatory deductions'],
        month=get_date_range().start
    ),
    BudgetCreate(
        name='regular pay', category='income', planned_amount=0,
        description='Regular monthly income',
        examples=['base pay'],
        month=get_date_range().start
    ),
    BudgetCreate(
        name='non-regular pay', category='income', planned_amount=0,
        description='incomes aside from regular monthly salary',
        examples=['side jobs', 'bonus'],
        month=get_date_range().start
    ),
]
