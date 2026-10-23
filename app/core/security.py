"""Password hashing and JWT helpers."""
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.constants import (
    CLAIM_EXPIRES,
    CLAIM_ROLE,
    CLAIM_SUBJECT,
    CLAIM_USER_ID,
    JWT_ALGORITHM,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(username: str, user_id: str, role: str, expires_delta: timedelta | None = None) -> str:
    expires_delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        CLAIM_SUBJECT: username,
        CLAIM_USER_ID: user_id,
        CLAIM_ROLE: role,
        CLAIM_EXPIRES: datetime.now(timezone.utc) + expires_delta,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Return the token's claims. Raises jose.JWTError if invalid or expired."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])
