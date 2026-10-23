from fastapi import APIRouter, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.core.constants import TODO_NOT_FOUND, TODOS_PREFIX, TODOS_TAG
from app.db.models import Todos, Users
from app.dependencies import CurrentUser, DbSession
from app.schemas.todo import TodoRequest, TodoResponse

router = APIRouter(prefix=TODOS_PREFIX, tags=[TODOS_TAG])


def get_owned_todo_or_404(db: Session, todo_id: int, user: Users) -> Todos:
    """Users can only see their own todos; someone else's todo looks like a 404."""
    todo = db.query(Todos).filter(Todos.id == todo_id, Todos.owner_id == user.id).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=TODO_NOT_FOUND.format(todo_id=todo_id))
    return todo


@router.get("", response_model=list[TodoResponse], status_code=status.HTTP_200_OK)
def read_all(user: CurrentUser, db: DbSession):
    return db.query(Todos).filter(Todos.owner_id == user.id).all()


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(todo: TodoRequest, user: CurrentUser, db: DbSession):
    db_todo = Todos(**todo.model_dump(), owner_id=user.id)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo


@router.get("/{todo_id}", response_model=TodoResponse, status_code=status.HTTP_200_OK)
def read_todo(user: CurrentUser, db: DbSession, todo_id: int = Path(gt=0)):
    return get_owned_todo_or_404(db, todo_id, user)


@router.put("/{todo_id}", response_model=TodoResponse, status_code=status.HTTP_200_OK)
def update_todo(todo: TodoRequest, user: CurrentUser, db: DbSession, todo_id: int = Path(gt=0)):
    db_todo = get_owned_todo_or_404(db, todo_id, user)
    for key, value in todo.model_dump().items():
        setattr(db_todo, key, value)
    db.commit()
    db.refresh(db_todo)
    return db_todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(user: CurrentUser, db: DbSession, todo_id: int = Path(gt=0)):
    db_todo = get_owned_todo_or_404(db, todo_id, user)
    db.delete(db_todo)
    db.commit()
