"""Shared FastAPI dependencies.

Routes declare what they need (a DB session, the current user, an admin) and FastAPI
builds and injects it per request. Tests swap these out via app.dependency_overrides.
"""
from typing import Annotated, Iterator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.constants import (
    CLAIM_SUBJECT,
    CLAIM_USER_ID,
    COULD_NOT_VALIDATE_CREDENTIALS,
    INSUFFICIENT_PERMISSIONS,
    ROLE_ADMIN,
    TOKEN_URL,
)
from app.core.security import decode_access_token
from app.db.database import SessionLocal
from app.db.models import Users

oauth2_bearer = OAuth2PasswordBearer(tokenUrl=TOKEN_URL)


def get_db() -> Iterator[Session]:
    """Open one session per request and always close it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(token: Annotated[str, Depends(oauth2_bearer)], db: DbSession) -> Users:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=COULD_NOT_VALIDATE_CREDENTIALS,
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise credentials_exception

    username = payload.get(CLAIM_SUBJECT)
    user_id = payload.get(CLAIM_USER_ID)
    if username is None or user_id is None:
        raise credentials_exception

    user = db.query(Users).filter(Users.username == username, Users.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


CurrentUser = Annotated[Users, Depends(get_current_user)]


def get_current_admin(user: CurrentUser) -> Users:
    """Dependency chain: requires a valid token (get_current_user) AND the admin role."""
    if user.role != ROLE_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=INSUFFICIENT_PERMISSIONS)
    return user


AdminUser = Annotated[Users, Depends(get_current_admin)]
