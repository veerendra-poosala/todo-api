"""Shared FastAPI dependencies.

Routes declare what they need (the current user, an admin) and FastAPI builds and
injects it per request. Tests swap these out via app.dependency_overrides.

There is no get_db here: Beanie documents query the database directly once
init_beanie() has run at startup (see app/main.py lifespan).
"""
from typing import Annotated

from beanie import PydanticObjectId
from bson.errors import InvalidId
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from app.core.constants import (
    CLAIM_SUBJECT,
    CLAIM_USER_ID,
    COULD_NOT_VALIDATE_CREDENTIALS,
    INSUFFICIENT_PERMISSIONS,
    ROLE_ADMIN,
    TOKEN_URL,
)
from app.core.security import decode_access_token
from app.db.models import Users

oauth2_bearer = OAuth2PasswordBearer(tokenUrl=TOKEN_URL)


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]) -> Users:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=COULD_NOT_VALIDATE_CREDENTIALS,
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        username = payload.get(CLAIM_SUBJECT)
        user_id = PydanticObjectId(payload.get(CLAIM_USER_ID))
    except (JWTError, InvalidId, TypeError):
        raise credentials_exception

    if username is None:
        raise credentials_exception

    user = await Users.find_one(Users.id == user_id, Users.username == username)
    if user is None:
        raise credentials_exception
    return user


CurrentUser = Annotated[Users, Depends(get_current_user)]


async def get_current_admin(user: CurrentUser) -> Users:
    """Dependency chain: requires a valid token (get_current_user) AND the admin role."""
    if user.role != ROLE_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=INSUFFICIENT_PERMISSIONS)
    return user


AdminUser = Annotated[Users, Depends(get_current_admin)]
