from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import (
    TODO_DESCRIPTION_MAX_LENGTH,
    TODO_DESCRIPTION_MIN_LENGTH,
    TODO_PRIORITY_MAX,
    TODO_PRIORITY_MIN,
    TODO_TITLE_MAX_LENGTH,
    TODO_TITLE_MIN_LENGTH,
)


class TodoRequest(BaseModel):
    title: str = Field(min_length=TODO_TITLE_MIN_LENGTH, max_length=TODO_TITLE_MAX_LENGTH)
    description: str = Field(min_length=TODO_DESCRIPTION_MIN_LENGTH, max_length=TODO_DESCRIPTION_MAX_LENGTH)
    priority: int = Field(ge=TODO_PRIORITY_MIN, le=TODO_PRIORITY_MAX)
    complete: bool = False


class TodoResponse(BaseModel):
    # from_attributes lets Pydantic read values from a Beanie document.
    model_config = ConfigDict(from_attributes=True)

    # ObjectIds are serialised to JSON as 24-character hex strings.
    id: PydanticObjectId
    title: str
    description: str
    priority: int
    complete: bool
    owner_id: PydanticObjectId
