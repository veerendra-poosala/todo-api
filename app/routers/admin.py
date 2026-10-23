from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, status

from app.core.constants import ADMIN_PREFIX, ADMIN_TAG, TODO_NOT_FOUND
from app.db.models import Todos
from app.dependencies import AdminUser
from app.schemas.todo import TodoResponse

router = APIRouter(prefix=ADMIN_PREFIX, tags=[ADMIN_TAG])


@router.get("/todo", response_model=list[TodoResponse], status_code=status.HTTP_200_OK)
async def read_all_todos(_admin: AdminUser):
    return await Todos.find_all().to_list()


@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(todo_id: PydanticObjectId, _admin: AdminUser):
    db_todo = await Todos.get(todo_id)
    if db_todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=TODO_NOT_FOUND.format(todo_id=todo_id))
    await db_todo.delete()
