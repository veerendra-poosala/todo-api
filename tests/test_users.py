from fastapi import status

from app.core.constants import INCORRECT_CURRENT_PASSWORD
from app.core.security import verify_password
from app.db.models import Users

from .utils import TEST_USER_PASSWORD


async def test_get_user_details(client, test_user):
    response = await client.get("/user/get-user-details")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email
    assert data["role"] == test_user.role
    assert data["phone_number"] == test_user.phone_number
    assert "hashed_password" not in data  # response_model must hide the hash


async def test_update_phone_number(client, test_user):
    response = await client.put("/user/update-phone-number", json={"phone_number": "2222222222"})
    assert response.status_code == status.HTTP_200_OK
    assert (await Users.get(test_user.id)).phone_number == "2222222222"


async def test_update_phone_number_invalid(client, test_user):
    response = await client.put("/user/update-phone-number", json={"phone_number": "123"})  # too short (min 10)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_change_password(client, test_user):
    payload = {"current_password": TEST_USER_PASSWORD, "new_password": "newpassword123"}
    response = await client.put("/user/change-password", json=payload)
    assert response.status_code == status.HTTP_200_OK
    assert verify_password("newpassword123", (await Users.get(test_user.id)).hashed_password)


async def test_change_password_wrong_current_password(client, test_user):
    payload = {"current_password": "wrongpassword", "new_password": "newpassword123"}
    response = await client.put("/user/change-password", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": INCORRECT_CURRENT_PASSWORD}
    assert verify_password(TEST_USER_PASSWORD, (await Users.get(test_user.id)).hashed_password)


async def test_change_password_same_as_current(client, test_user):
    payload = {"current_password": TEST_USER_PASSWORD, "new_password": TEST_USER_PASSWORD}
    response = await client.put("/user/change-password", json=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


async def test_change_password_too_short(client, test_user):
    payload = {"current_password": TEST_USER_PASSWORD, "new_password": "abc"}
    response = await client.put("/user/change-password", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
