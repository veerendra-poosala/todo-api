from fastapi import APIRouter, HTTPException, Path, status

from app.core.constants import ADMIN_PREFIX, ADMIN_TAG, TODO_NOT_FOUND
from app.db.models import Todos
from app.dependencies import AdminUser, DbSession
from app.schemas.todo import TodoResponse

router = APIRouter(prefix=ADMIN_PREFIX, tags=[ADMIN_TAG])


@router.get("/todo", response_model=list[TodoResponse], status_code=status.HTTP_200_OK)
def read_all_todos(_admin: AdminUser, db: DbSession):
    return db.query(Todos).all()


@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(_admin: AdminUser, db: DbSession, todo_id: int = Path(gt=0)):
    db_todo = db.query(Todos).filter(Todos.id == todo_id).first()
    if db_todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=TODO_NOT_FOUND.format(todo_id=todo_id))
    db.delete(db_todo)
    db.commit()
