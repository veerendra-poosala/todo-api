"""Database engine, session factory and declarative Base (SQLAlchemy)."""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# SQLite only allows a connection to be used by the thread that created it;
# FastAPI serves requests from a thread pool, so that check is disabled for SQLite.
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

# The engine owns the connection pool. pool_pre_ping drops dead connections
# (e.g. after MySQL's wait_timeout) instead of failing the next request.
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

# Each request gets its own Session from this factory (see app/dependencies.py).
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# All ORM models inherit from Base; Base.metadata is what Alembic compares against.
Base = declarative_base()
