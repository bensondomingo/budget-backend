import uuid
from datetime import date

from sqlalchemy import (Column, Date, Enum, Float, ForeignKey, func,
                        String, TIMESTAMP, UniqueConstraint)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.services.utils import get_date_range
from .schemas import BudgetCategoryEnum


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
