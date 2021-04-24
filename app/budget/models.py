import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (Column, Enum, Float, ForeignKey,
                        String, TIMESTAMP, UniqueConstraint)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Date

from app.core.database import Base
from app.services.utils import get_default_date_range
from .schemas import BudgetCategoryEnum


class Budget(Base):
    """ Docs later """
    __tablename__ = 'budgets'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), index=True, nullable=False)
    category = Column(Enum(BudgetCategoryEnum), index=True, nullable=False)
    description = Column(String(200))
    examples = Column(String(300))
    planned_amount = Column(Float, nullable=False)
    month = Column(Date, default=get_default_date_range().start)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow())
    updated_at = Column(TIMESTAMP(timezone=True),
                        default=datetime.utcnow(), onupdate=datetime.utcnow())

    # Foreign Keys
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))

    # Relationships
    transactions = relationship('Transaction', backref='budgets')

    __table_args__ = (
        UniqueConstraint('name', 'month'),
    )


class Transaction(Base):
    """ Docs later """
    __tablename__ = 'transactions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(Date, default=date.today())
    amount = Column(Float, nullable=False)
    description = Column(String(100), nullable=False)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow())
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.now(
        timezone.utc), onupdate=datetime.utcnow())

    # Foreign Keys
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    budget_id = Column(UUID(as_uuid=True), ForeignKey('budgets.id'))
