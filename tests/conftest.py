import os

from .utils import TEST_MONGODB_DB, TEST_USER_PASSWORD, mongo_is_available

# Settings are read when the app is imported, so point them at the test database first.
# MONGODB_DB is forced so tests can never touch the real database from .env.
os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")
os.environ["MONGODB_DB"] = TEST_MONGODB_DB
os.environ.setdefault("SECRET_KEY", "test-secret-key")

import pytest  # noqa: E402 - must come after the environment is configured
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.constants import ROLE_ADMIN  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.models import DOCUMENT_MODELS, Todos, Users  # noqa: E402
from app.db.mongo import init_db  # noqa: E402
from app.dependencies import get_current_user  # noqa: E402
from app.main import app  # noqa: E402

MONGO_AVAILABLE = mongo_is_available(settings.MONGODB_URL)


@pytest.fixture
async def mongo_db():
    """Connect Beanie to an empty test database for every test, then drop it."""
    if not MONGO_AVAILABLE:
        pytest.skip(f"MongoDB not reachable at {settings.MONGODB_URL} (run: docker compose up -d mongo)")
    client = await init_db(settings.MONGODB_URL, settings.MONGODB_DB)
    for model in DOCUMENT_MODELS:
        await model.delete_all()
    yield
    await client.drop_database(settings.MONGODB_DB)
    await client.close()


@pytest.fixture
async def client(mongo_db):
    # ASGITransport calls the app in-process, on the same event loop as the test.
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        yield async_client


@pytest.fixture
async def test_user(mongo_db):
    user = await Users(
        username="testuser",
        email="testuser@example.com",
        first_name="Test",
        last_name="User",
        hashed_password=hash_password(TEST_USER_PASSWORD),
        role=ROLE_ADMIN,
        phone_number="1111111111",
    ).insert()
    app.dependency_overrides[get_current_user] = lambda: user
    yield user
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
async def test_todo(test_user):
    return await Todos(
        title="Test Todo",
        description="This is a test todo",
        priority=1,
        complete=False,
        owner_id=test_user.id,
    ).insert()
