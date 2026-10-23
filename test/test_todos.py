
from fastapi import status
from sqlalchemy.pool import StaticPool
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import pytest

from database import Base
from main import app
from models import Users, Todos
from routers.todos import get_db
from routers.auth import get_current_user

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"  # Use a separate test database

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)  # Create tables in the test database


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_get_current_user():
    return {"id": 1, "username": "testuser", "role": "admin"}  # Mocked user for testing


app.dependency_overrides[get_db] = override_get_db  # Override the get_db dependency for testing
app.dependency_overrides[get_current_user] = override_get_current_user  # Override the get_current_user dependency for testing

client = TestClient(app)  # Create a TestClient instance for testing the FastAPI app

@pytest.fixture(autouse=True)
def test_todo():
    todo = Todos(title="Test Todo", description="This is a test todo", priority=1, complete=False, owner_id=1)
    db = TestingSessionLocal()
    db.add(todo)
    db.commit()
    yield todo
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM todos"))  # Clean up the todos table after each test
        connection.commit()

def test_read_all_authenticated(test_todo):
    response = client.get("/todo/1")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{
        "id": test_todo.id, 
        "title": test_todo.title,
        "description": test_todo.description,
        "priority": test_todo.priority,
        "complete": test_todo.complete,
        "owner_id": test_todo.owner_id
    }]

def test_read_one_authenticated(test_todo):
    response = client.get(f"/{test_todo.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "id": test_todo.id, 
        "title": test_todo.title,
        "description": test_todo.description,
        "priority": test_todo.priority,
        "complete": test_todo.complete,
        "owner_id": test_todo.owner_id
    }