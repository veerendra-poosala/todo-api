
from database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String(255), unique=True)
    username = Column(String(100), unique=True)

    first_name = Column(String(100))
    last_name = Column(String(100))

    # Store the hashed password, not the original password.
    # 255 characters provides room for common password hash formats.
    hashed_password = Column(String(255))

    is_active = Column(Boolean, default=True)

    # Default role is "user".
    role = Column(String(50), default="user")

    # New column for phone number.
    phone_number = Column(String(20), nullable=True)


class Todos(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(200))
    description = Column(String(1000))

    priority = Column(Integer)
    complete = Column(Boolean, default=False)

    # Foreign key referencing the users table.
    owner_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )
