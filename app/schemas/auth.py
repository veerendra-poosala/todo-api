from pydantic import BaseModel, EmailStr, Field

from app.core.constants import PASSWORD_MIN_LENGTH, ROLE_USER


class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    password: str = Field(min_length=PASSWORD_MIN_LENGTH)
    role: str = ROLE_USER


class CreateUserResponse(BaseModel):
    message: str
    user_id: int


class Token(BaseModel):
    access_token: str
    token_type: str
