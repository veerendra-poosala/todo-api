"""SQLAlchemy ORM models — each class maps to one database table."""
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String

from app.core.constants import ROLE_USER
from app.db.database import Base


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True)
    username = Column(String(100), unique=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    # Only the bcrypt hash is stored, never the plain password.
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    role = Column(String(50), default=ROLE_USER)
    phone_number = Column(String(20), nullable=True)


class Todos(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200))
    description = Column(String(1000))
    priority = Column(Integer)
    complete = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
