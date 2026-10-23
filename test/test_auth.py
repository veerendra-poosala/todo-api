
import asyncio
from datetime import timedelta

import pytest
from fastapi import HTTPException, status
from jose import jwt

from models import Users
from routers.auth import (
    ALGORITHM,
    SECRET_KEY,
    authenticate_user,
    create_access_token,
    get_current_user,
)

from .utils import client, TestingSessionLocal, TEST_USER_PASSWORD


def test_create_user():
    new_user = {
        "username": "newuser",
        "email": "newuser@example.com",
        "first_name": "New",
        "last_name": "User",
        "password": "password123"
    }
    response = client.post("/auth/user", json=new_user)
    assert response.status_code == status.HTTP_201_CREATED

    db = TestingSessionLocal()
    created = db.query(Users).filter(Users.username == "newuser").first()
    db.close()
    assert created is not None
    assert created.role == "user"
    assert created.hashed_password != new_user["password"]


def test_create_user_duplicate(test_user):
    duplicate_user = {
        "username": test_user.username,
        "email": "other@example.com",
        "first_name": "Dup",
        "last_name": "User",
        "password": "password123"
    }
    response = client.post("/auth/user", json=duplicate_user)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_create_user_missing_fields():
    response = client.post("/auth/user", json={"username": "incomplete"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_login_for_access_token(test_user):
    login_data = {"username": test_user.username, "password": TEST_USER_PASSWORD}
    response = client.post("/auth/token", data=login_data)
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_invalid_password(test_user):
    login_data = {"username": test_user.username, "password": "wrongpassword"}
    response = client.post("/auth/token", data=login_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_authenticate_user(test_user):
    db = TestingSessionLocal()
    try:
        authenticated = authenticate_user(db, test_user.username, TEST_USER_PASSWORD)
        assert authenticated.id == test_user.id
        assert authenticate_user(db, "unknown", TEST_USER_PASSWORD) is False
        assert authenticate_user(db, test_user.username, "wrongpassword") is False
    finally:
        db.close()


def test_create_access_token():
    token = create_access_token("testuser", 1, "admin", timedelta(minutes=5))
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "testuser"
    assert payload["user_id"] == 1
    assert payload["role"] == "admin"
    assert "exp" in payload


def test_get_current_user_valid_token(test_user):
    token = create_access_token(test_user.username, test_user.id, test_user.role, timedelta(minutes=5))
    db = TestingSessionLocal()
    try:
        user = asyncio.run(get_current_user(token=token, db=db))
        assert user.id == test_user.id
        assert user.username == test_user.username
    finally:
        db.close()


def test_get_current_user_invalid_token():
    db = TestingSessionLocal()
    try:
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_current_user(token="not-a-valid-token", db=db))
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    finally:
        db.close()


def test_get_current_user_missing_claims():
    token = jwt.encode({"role": "admin"}, SECRET_KEY, algorithm=ALGORITHM)
    db = TestingSessionLocal()
    try:
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_current_user(token=token, db=db))
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    finally:
        db.close()
