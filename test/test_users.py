
from fastapi import status

from models import Users
from routers.auth import bcrypt_context

from .utils import client, TestingSessionLocal, TEST_USER_PASSWORD


def get_user_from_db(user_id):
    db = TestingSessionLocal()
    try:
        return db.query(Users).filter(Users.id == user_id).first()
    finally:
        db.close()


def test_get_user_details(test_user):
    response = client.get("/user/get-user-details")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_user.id
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email
    assert data["role"] == test_user.role
    assert data["phone_number"] == test_user.phone_number


def test_update_phone_number(test_user):
    response = client.put("/user/update-phone-number", json={"phone_number": "2222222222"})
    assert response.status_code == status.HTTP_200_OK
    assert get_user_from_db(test_user.id).phone_number == "2222222222"


def test_update_phone_number_invalid():
    response = client.put("/user/update-phone-number", json={"phone_number": "123"})  # too short (min 10)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_change_password(test_user):
    payload = {"current_password": TEST_USER_PASSWORD, "new_password": "newpassword123"}
    response = client.put("/user/change-password", json=payload)
    assert response.status_code == status.HTTP_200_OK
    updated = get_user_from_db(test_user.id)
    assert bcrypt_context.verify("newpassword123", updated.hashed_password)


def test_change_password_wrong_current_password(test_user):
    payload = {"current_password": "wrongpassword", "new_password": "newpassword123"}
    response = client.put("/user/change-password", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Incorrect current password"}
    unchanged = get_user_from_db(test_user.id)
    assert bcrypt_context.verify(TEST_USER_PASSWORD, unchanged.hashed_password)


def test_change_password_same_as_current():
    payload = {"current_password": TEST_USER_PASSWORD, "new_password": TEST_USER_PASSWORD}
    response = client.put("/user/change-password", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_change_password_too_short():
    payload = {"current_password": TEST_USER_PASSWORD, "new_password": "abc"}
    response = client.put("/user/change-password", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
