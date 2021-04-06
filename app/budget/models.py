import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from .schemas import BudgetCategoryEnum


class Budget(Base):
    """ Docs later """
    __tablename__ = 'budgets'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, index=True, nullable=False)
    category = Column(Enum(BudgetCategoryEnum), index=True, nullable=False)
    planned_amount = Column(Float, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(
        timezone.utc), onupdate=datetime.now(timezone.utc))

    # Foreign Keys
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))

    # Relationships
    transactions = relationship('Transaction', backref='budgets')


class Transaction(Base):
    """ Docs later """
    __tablename__ = 'transactions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    amount = Column(Float, nullable=False)
    description = Column(String(100), nullable=False)
    date = Column(DateTime, default=datetime.now(timezone.utc))

    # Timestamps
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(
        timezone.utc), onupdate=datetime.now(timezone.utc))

    # Foreign Keys
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    budget_id = Column(UUID(as_uuid=True), ForeignKey('budgets.id'))
