
# Import HTTPException to return HTTP errors, such as 404 Not Found.
# Import status constants, such as 200, 201, 204, and 404.
# Import Depends to inject dependencies, such as a database session.
from fastapi import APIRouter, HTTPException, status, Depends

# Import Annotated to combine a Python type with dependency metadata.
from typing import Annotated

# Import Session to specify the SQLAlchemy database session type.
from sqlalchemy.orm import Session

# Import the Todos model class representing the todos database table.
from models import Todos

# Import the database engine and session factory from database.py.
from database import SessionLocal

from .auth import get_current_user  # Import the get_current_user function for user authentication.

# Create the FastAPI application instance.
router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)



# Define a dependency function that provides a database session.
def get_db():

    # Create a new database session using the SessionLocal factory.
    db = SessionLocal()

    try:
        # yield provides the session to the API endpoint that requests it.
        # FastAPI runs the endpoint using this database session.
        yield db

    finally:
        # Close the session after the request finishes, including when an error occurs.
        db.close()


# Define a reusable database dependency.
# Session specifies the expected type of the database session.
# Depends(get_db) tells FastAPI to call get_db and inject its yielded session.
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]  # Dependency for authenticated user

@router.get("/todo", status_code=status.HTTP_200_OK)
async def get_todos(db: db_dependency, user: user_dependency):
    if user is None or user.role != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed or Insufficient Permissions")
    return db.query(Todos).all()


@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(todo_id: int, db: db_dependency, user: user_dependency):
    if user is None or user.role != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed or Insufficient Permissions")
    db_todo = db.query(Todos).filter(Todos.id == todo_id).first()
    if not db_todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    db.delete(db_todo)
    db.commit()
    return {"detail": "Todo deleted successfully"}