import uuid
from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.engine import Base


class User(Base):
    """ Users model - Represents a single user of tha application """
    __tablename__ = 'users'

    # id = Column(UUID(as_uuid=True), primary_key=True,
    #             default=uuid.uuid4, index=True)
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    # relationships
    budgets = relationship('Budget', backref='user')


class Budget(Base):
    """ Docs later """
    __tablename__ = 'budgets'

    # id = Column(UUID(as_uuid=True), primary_key=True,
    #             default=uuid.uuid4, index=True)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True)
    category = Column(String(50), index=True)
    planned_amount = Column(Float)
    user_id = Column(Integer, ForeignKey('users.id'))


# class Transaction(Base):
#     """ Docs later """
#     __tablename__ = 'transactions'


# class Item(Base):
#     """ Items models """
#     __tablename__ = 'items'

#     id = Column(Integer, primary_key=True, index=True)
#     title = Column(String, index=True)
#     description = Column(String, index=True)
#     owner_id = Column(Integer, ForeignKey('users.id'))
#     owner = relationship('User', back_populates='items')
