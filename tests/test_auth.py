from datetime import timedelta

import pytest
from beanie import PydanticObjectId
from fastapi import HTTPException, status
from jose import jwt

from app.core.config import settings
from app.core.constants import (
    CLAIM_ROLE,
    CLAIM_SUBJECT,
    CLAIM_USER_ID,
    JWT_ALGORITHM,
    ROLE_ADMIN,
    ROLE_USER,
    TOKEN_TYPE_BEARER,
    USER_ALREADY_EXISTS,
)
from app.core.security import create_access_token
from app.db.models import Users
from app.dependencies import get_current_user
from app.routers.auth import authenticate_user

from .utils import TEST_USER_PASSWORD


async def test_create_user(client):
    new_user = {
        "username": "newuser",
        "email": "newuser@example.com",
        "first_name": "New",
        "last_name": "User",
        "password": "password123"
    }
    response = await client.post("/auth/user", json=new_user)
    assert response.status_code == status.HTTP_201_CREATED

    created = await Users.find_one(Users.username == "newuser")
    assert created is not None
    assert str(created.id) == response.json()["user_id"]
    assert created.role == ROLE_USER
    assert created.hashed_password != new_user["password"]


async def test_create_user_duplicate(client, test_user):
    duplicate_user = {
        "username": test_user.username,
        "email": "other@example.com",
        "first_name": "Dup",
        "last_name": "User",
        "password": "password123"
    }
    response = await client.post("/auth/user", json=duplicate_user)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": USER_ALREADY_EXISTS}


async def test_create_user_missing_fields(client):
    response = await client.post("/auth/user", json={"username": "incomplete"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_login_for_access_token(client, test_user):
    login_data = {"username": test_user.username, "password": TEST_USER_PASSWORD}
    response = await client.post("/auth/token", data=login_data)
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()
    assert response.json()["token_type"] == TOKEN_TYPE_BEARER


async def test_login_invalid_password(client, test_user):
    login_data = {"username": test_user.username, "password": "wrongpassword"}
    response = await client.post("/auth/token", data=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_authenticate_user(test_user):
    authenticated = await authenticate_user(test_user.username, TEST_USER_PASSWORD)
    assert authenticated.id == test_user.id
    assert await authenticate_user("unknown", TEST_USER_PASSWORD) is None
    assert await authenticate_user(test_user.username, "wrongpassword") is None


def test_create_access_token():
    user_id = str(PydanticObjectId())
    token = create_access_token("testuser", user_id, ROLE_ADMIN, timedelta(minutes=5))
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])
    assert payload[CLAIM_SUBJECT] == "testuser"
    assert payload[CLAIM_USER_ID] == user_id
    assert payload[CLAIM_ROLE] == ROLE_ADMIN
    assert "exp" in payload


async def test_get_current_user_valid_token(test_user):
    token = create_access_token(test_user.username, str(test_user.id), test_user.role, timedelta(minutes=5))
    user = await get_current_user(token=token)
    assert user.id == test_user.id


@pytest.mark.parametrize("token_factory", [
    pytest.param(lambda u: create_access_token(u.username, str(u.id), u.role, timedelta(minutes=-1)), id="expired"),
    pytest.param(lambda u: "not-a-valid-token", id="garbage"),
    pytest.param(lambda u: jwt.encode({CLAIM_ROLE: ROLE_ADMIN}, settings.SECRET_KEY, algorithm=JWT_ALGORITHM),
                 id="missing-claims"),
    pytest.param(lambda u: create_access_token(u.username, "not-an-object-id", u.role), id="bad-user-id"),
])
async def test_get_current_user_rejects_bad_tokens(test_user, token_factory):
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token=token_factory(test_user))
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
