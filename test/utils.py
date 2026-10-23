
from sqlalchemy.pool import StaticPool
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from database import Base
from main import app
from models import Users

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"  # Use a separate test database

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)  # Create tables in the test database

TEST_USER_ID = 1
TEST_USER_PASSWORD = "testpassword"


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_current_user():
    # Return a real Users row (like the production dependency does), not a dict,
    # so routes can use attribute access such as user.id and user.role.
    db = TestingSessionLocal()
    try:
        return db.query(Users).filter(Users.id == TEST_USER_ID).first()
    finally:
        db.close()


client = TestClient(app)  # Create a TestClient instance for testing the FastAPI app
