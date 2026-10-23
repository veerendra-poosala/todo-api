from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, status

from app.core.constants import TODO_NOT_FOUND, TODOS_PREFIX, TODOS_TAG
from app.db.models import Todos, Users
from app.dependencies import CurrentUser
from app.schemas.todo import TodoRequest, TodoResponse

router = APIRouter(prefix=TODOS_PREFIX, tags=[TODOS_TAG])


async def get_owned_todo_or_404(todo_id: PydanticObjectId, user: Users) -> Todos:
    """Users can only see their own todos; someone else's todo looks like a 404."""
    todo = await Todos.find_one(Todos.id == todo_id, Todos.owner_id == user.id)
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=TODO_NOT_FOUND.format(todo_id=todo_id))
    return todo


@router.get("", response_model=list[TodoResponse], status_code=status.HTTP_200_OK)
async def read_all(user: CurrentUser):
    return await Todos.find(Todos.owner_id == user.id).to_list()


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_todo(todo: TodoRequest, user: CurrentUser):
    return await Todos(**todo.model_dump(), owner_id=user.id).insert()


# PydanticObjectId in the path: malformed ids are rejected with 422 before the route runs.
@router.get("/{todo_id}", response_model=TodoResponse, status_code=status.HTTP_200_OK)
async def read_todo(todo_id: PydanticObjectId, user: CurrentUser):
    return await get_owned_todo_or_404(todo_id, user)


@router.put("/{todo_id}", response_model=TodoResponse, status_code=status.HTTP_200_OK)
async def update_todo(todo_id: PydanticObjectId, todo: TodoRequest, user: CurrentUser):
    db_todo = await get_owned_todo_or_404(todo_id, user)
    for key, value in todo.model_dump().items():
        setattr(db_todo, key, value)
    await db_todo.save()
    return db_todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(todo_id: PydanticObjectId, user: CurrentUser):
    db_todo = await get_owned_todo_or_404(todo_id, user)
    await db_todo.delete()
