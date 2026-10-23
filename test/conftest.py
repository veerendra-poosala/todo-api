
import pytest
from sqlalchemy import text

from main import app
from models import Users, Todos
from routers import auth, todos, admin, users
from routers.auth import bcrypt_context, get_current_user

from .utils import (
    engine,
    TestingSessionLocal,
    override_get_db,
    override_get_current_user,
    TEST_USER_ID,
    TEST_USER_PASSWORD,
)

# Every router defines its own get_db, so each one must be overridden.
for router_module in (auth, todos, admin, users):
    app.dependency_overrides[router_module.get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


def clear_tables():
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM todos"))
        connection.execute(text("DELETE FROM users"))
        connection.commit()


@pytest.fixture(autouse=True)
def test_user():
    clear_tables()  # Remove leftovers from interrupted earlier runs
    user = Users(
        id=TEST_USER_ID,
        username="testuser",
        email="testuser@example.com",
        first_name="Test",
        last_name="User",
        hashed_password=bcrypt_context.hash(TEST_USER_PASSWORD),
        role="admin",
        phone_number="1111111111",
        is_active=True,
    )
    db = TestingSessionLocal()
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    yield user
    clear_tables()


@pytest.fixture
def test_todo(test_user):
    todo = Todos(
        title="Test Todo",
        description="This is a test todo",
        priority=1,
        complete=False,
        owner_id=test_user.id,
    )
    db = TestingSessionLocal()
    db.add(todo)
    db.commit()
    db.refresh(todo)
    db.close()
    yield todo
