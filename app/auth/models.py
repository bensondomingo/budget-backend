import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, TIMESTAMP, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    """ Users model - Represents a single user of tha application """
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow())
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow(),
                        onupdate=datetime.utcnow())

    # Relationships
    budgets = relationship('Budget', backref='users',
                           cascade='all, delete-orphan')
    transactions = relationship(
        'Transaction', backref='users', cascade='all, delete-orphan')
