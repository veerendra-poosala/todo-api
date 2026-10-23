"""Beanie documents — each class maps to one MongoDB collection.

Documents are Pydantic models, so the same type hints that validate API input
also describe what is stored. MongoDB adds the `_id` (ObjectId) automatically.
"""
from typing import Annotated

from beanie import Document, Indexed, PydanticObjectId

from app.core.constants import ROLE_USER


class Users(Document):
    username: Annotated[str, Indexed(unique=True)]
    email: Annotated[str, Indexed(unique=True)]
    first_name: str
    last_name: str
    # Only the bcrypt hash is stored, never the plain password.
    hashed_password: str
    is_active: bool = True
    role: str = ROLE_USER
    phone_number: str | None = None

    class Settings:
        name = "users"


class Todos(Document):
    title: str
    description: str
    priority: int
    complete: bool = False
    # A reference by id: MongoDB has no foreign keys, so the app keeps this consistent.
    owner_id: Annotated[PydanticObjectId, Indexed()]

    class Settings:
        name = "todos"


DOCUMENT_MODELS = [Users, Todos]
