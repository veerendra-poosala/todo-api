from fastapi import APIRouter, HTTPException, status

from app.core.constants import (
    INCORRECT_CURRENT_PASSWORD,
    PASSWORD_CHANGED,
    PASSWORD_MUST_DIFFER,
    PHONE_NUMBER_UPDATED,
    USERS_PREFIX,
    USERS_TAG,
)
from app.core.security import hash_password, verify_password
from app.dependencies import CurrentUser, DbSession
from app.schemas.user import ChangePasswordRequest, MessageResponse, PhoneNumberRequest, UserResponse

router = APIRouter(prefix=USERS_PREFIX, tags=[USERS_TAG])


@router.get("/get-user-details", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_user(user: CurrentUser):
    return user


@router.put("/change-password", response_model=MessageResponse, status_code=status.HTTP_200_OK)
def change_password(request: ChangePasswordRequest, user: CurrentUser, db: DbSession):
    if not verify_password(request.current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=INCORRECT_CURRENT_PASSWORD)
    if request.new_password == request.current_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=PASSWORD_MUST_DIFFER)
    user.hashed_password = hash_password(request.new_password)
    db.add(user)
    db.commit()
    return MessageResponse(message=PASSWORD_CHANGED)


@router.put("/update-phone-number", response_model=MessageResponse, status_code=status.HTTP_200_OK)
def update_phone_number(request: PhoneNumberRequest, user: CurrentUser, db: DbSession):
    user.phone_number = request.phone_number
    db.add(user)
    db.commit()
    return MessageResponse(message=PHONE_NUMBER_UPDATED)
