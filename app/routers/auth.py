from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

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
from app.dependencies import DbSession
from app.schemas.auth import CreateUserRequest, CreateUserResponse, Token

router = APIRouter(prefix=AUTH_PREFIX, tags=[AUTH_TAG])


def authenticate_user(db: Session, username: str, password: str) -> Users | None:
    user = db.query(Users).filter(Users.username == username).first()
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user


@router.post("/user", response_model=CreateUserResponse, status_code=status.HTTP_201_CREATED)
def create_user(request: CreateUserRequest, db: DbSession):
    existing_user = (
        db.query(Users)
        .filter((Users.username == request.username) | (Users.email == request.email))
        .first()
    )
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=USER_ALREADY_EXISTS)

    new_user = Users(
        username=request.username,
        email=request.email,
        first_name=request.first_name,
        last_name=request.last_name,
        hashed_password=hash_password(request.password),
        role=request.role,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return CreateUserResponse(message=USER_CREATED, user_id=new_user.id)


@router.post("/token", response_model=Token, status_code=status.HTTP_200_OK)
def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession):
    user = authenticate_user(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS,
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(user.username, user.id, user.role)
    return Token(access_token=access_token, token_type=TOKEN_TYPE_BEARER)
