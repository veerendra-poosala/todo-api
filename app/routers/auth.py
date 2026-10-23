from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pymongo.errors import DuplicateKeyError

from app.core.constants import (
    AUTH_PREFIX,
    AUTH_TAG,
    INVALID_CREDENTIALS,
    TOKEN_TYPE_BEARER,
    USER_ALREADY_EXISTS,
    USER_CREATED,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import Users
from app.schemas.auth import CreateUserRequest, CreateUserResponse, Token

router = APIRouter(prefix=AUTH_PREFIX, tags=[AUTH_TAG])


async def authenticate_user(username: str, password: str) -> Users | None:
    user = await Users.find_one(Users.username == username)
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user


@router.post("/user", response_model=CreateUserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(request: CreateUserRequest):
    new_user = Users(
        username=request.username,
        email=request.email,
        first_name=request.first_name,
        last_name=request.last_name,
        hashed_password=hash_password(request.password),
        role=request.role,
    )
    try:
        # The unique indexes on username/email make the database the final judge,
        # which also covers two sign-ups racing each other.
        await new_user.insert()
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=USER_ALREADY_EXISTS)
    return CreateUserResponse(message=USER_CREATED, user_id=new_user.id)


@router.post("/token", response_model=Token, status_code=status.HTTP_200_OK)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = await authenticate_user(form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS,
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(user.username, str(user.id), user.role)
    return Token(access_token=access_token, token_type=TOKEN_TYPE_BEARER)
