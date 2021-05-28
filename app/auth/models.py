import uuid

from pydantic.types import UUID4  # pylint: disable=no-name-in-module
from sqlalchemy import Boolean, Column, func, TIMESTAMP, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.budget.models import Budget as BudgetModel, default_budgets
from app.core.database import Base, SessionLocal


class User(Base):
    """ Users model - Represents a single user of tha application """
    __tablename__ = 'user'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True),
                        server_default=func.now(), onupdate=func.now())

    # Relationships
    budgets = relationship('Budget', backref='user',
                           cascade='all, delete-orphan')
    transactions = relationship(
        'Transaction', backref='user', cascade='all, delete-orphan')

    __mapper_args__ = {"eager_defaults": True}


def post_signup(user_id: UUID4):

    def assign_user_id():
        for b in default_budgets:
            budget = BudgetModel(**b.dict(exclude_unset=True))
            budget.user_id = user_id
            yield budget

    with SessionLocal() as session:
        budgets = [*assign_user_id()]
        session.add_all(budgets)
        session.commit()
