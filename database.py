
# Import create_engine to create a connection interface between Python and the database.
from sqlalchemy import create_engine

# Import sessionmaker to create database sessions for executing queries and managing transactions.
from sqlalchemy.orm import sessionmaker

# Import declarative_base to create a base class for defining database models using Python classes.
from sqlalchemy.ext.declarative import declarative_base


# Define the database connection URL.
# sqlite:/// means we are using a SQLite database file.
# ./todosapp.db means the database file is stored in the current working directory.
SQLALCHEMY_DATABASE_URL = 'mysql+pymysql://root:root@localhost:3306/todoapplication'  # Update this URL to match your database configuration


# Create the SQLAlchemy engine, which manages database connectivity.
# SQLALCHEMY_DATABASE_URL tells SQLAlchemy which database to connect to.
# connect_args is used to pass database-specific connection settings.
# check_same_thread=False allows SQLite connections to be used across different threads.
# This setting is commonly used with FastAPI and SQLite.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)


# Create a session factory named SessionLocal.
# sessionmaker creates a factory that produces database session objects.
# autocommit=False means transactions are not committed automatically.
# autoflush=False means pending changes are not automatically flushed before queries.
# bind=engine associates every session created by this factory with our database engine.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Create a base class for defining SQLAlchemy ORM models.
# Database model classes inherit from Base.
# SQLAlchemy uses this base to track model definitions and their database table metadata.
Base = declarative_base()
