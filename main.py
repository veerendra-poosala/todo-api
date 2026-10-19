
# Import FastAPI to create and configure a web application.
from fastapi import HTTPException
from pydantic import Field
from pydantic import BaseModel
from fastapi import status
from fastapi import Depends
from typing import Annotated
from fastapi import FastAPI
from sqlalchemy.orm import Session

# Import the models module.
# This module contains the SQLAlchemy database models, such as a Todo model.
# Importing models also registers those model classes with SQLAlchemy's Base metadata.
import models
from models import Todos

# Import the database engine from database.py.
# The engine manages the connection to the configured database.
from database import engine, SessionLocal




# Create an instance of the FastAPI application.
# This app object is used to define API endpoints and handle incoming HTTP requests.
app = FastAPI()


# Create database tables for all models registered with models.Base.
# bind=engine tells SQLAlchemy which database to use.
# Existing tables are not recreated or overwritten.
# This works only for models that have already been imported and registered.
models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally: 
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

class TodoRequest(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    description: str = Field(min_length=3, max_length=200)
    priority: int = Field(ge=1, le=3)
    complete: bool = False

@app.get("/", status_code=status.HTTP_200_OK)
async def read_all(db: db_dependency): 
    return db.query(Todos).all() 


@app.post("/todo", status_code=status.HTTP_201_CREATED)
async def create_todo(db: db_dependency, todo: TodoRequest):
    db_todo = models.Todos(**todo.dict())
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo


@app.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def read_todo(todo_id: int, db: db_dependency):
    todo = db.query(Todos).filter(Todos.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Todo with id {todo_id} not found")
    return todo

@app.put("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def update_todo(todo_id: int, todo: TodoRequest, db: db_dependency):
    db_todo = db.query(Todos).filter(Todos.id == todo_id).first()
    if not db_todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Todo with id {todo_id} not found")
    for key, value in todo.dict().items():
        # print(f"Updating {key} to {value}")
        setattr(db_todo, key, value)
    db.commit()
    db.refresh(db_todo)
    return db_todo



@app.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(todo_id: int, db: db_dependency):
    db_todo = db.query(Todos).filter(Todos.id == todo_id).first()
    if not db_todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Todo with id {todo_id} not found")
    db.delete(db_todo)
    db.commit()
    return None