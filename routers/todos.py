
# Import HTTPException to return HTTP errors, such as 404 Not Found.
# Import status constants, such as 200, 201, 204, and 404.
# Import Depends to inject dependencies, such as a database session.
from fastapi import APIRouter, HTTPException, status, Depends


# Import Field to define validation rules for request data.
# Import BaseModel to create Pydantic models for request validation.
from pydantic import Field, BaseModel

# Import Annotated to combine a Python type with dependency metadata.
from typing import Annotated

# Import Session to specify the SQLAlchemy database session type.
from sqlalchemy.orm import Session

# Import the models module containing SQLAlchemy database models.
import models

# Import the Todos model class representing the todos database table.
from models import Todos

# Import the database engine and session factory from database.py.
from database import engine, SessionLocal
from routers import auth  # Import the auth router for authentication endpoints.

from .auth import get_current_user  # Import the get_current_user function for user authentication.

# Create the FastAPI application instance.
router = APIRouter()



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
user_dependency = Annotated[models.Users, Depends(get_current_user)]  # Dependency for authenticated user

# Define the expected structure and validation rules for todo request data.
class TodoRequest(BaseModel):

    # Require a title containing at least 3 and at most 100 characters.
    title: str = Field(min_length=3, max_length=100)

    # Require a description containing at least 3 and at most 200 characters.
    description: str = Field(min_length=3, max_length=200)

    # Require priority to be an integer from 1 through 3.
    priority: int = Field(ge=1, le=3)

    # Set complete to False when the client does not provide this field.
    complete: bool = False


# Register a GET endpoint at the root URL "/".
# Return HTTP 200 OK when the request succeeds.
@router.get("/", status_code=status.HTTP_200_OK)
def read_all(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    # Query the Todos table and return all matching database records.
    return db.query(Todos).filter(Todos.owner_id == user.id).all()  # Filter todos by the authenticated user's ID


# Register a POST endpoint at "/todo".
# Return HTTP 201 Created when a todo is successfully created.
@router.post("/todo", status_code=status.HTTP_201_CREATED)
def create_todo(user: user_dependency, db: db_dependency, todo: TodoRequest):

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    # Convert the validated Pydantic request data into a SQLAlchemy model.
    # model_dump() returns the request fields as a Python dictionary.
    # ** unpacks the dictionary into keyword arguments for the model constructor.
    db_todo = models.Todos(**todo.model_dump(), owner_id=user.id)  # Set the owner_id to the authenticated user's ID

    # Add the new todo object to the database session.
    db.add(db_todo)

    # Commit the transaction to save the new record to the database.
    db.commit()

    # Refresh the object with values currently stored in the database.
    # For example, this retrieves a database-generated ID.
    db.refresh(db_todo)

    # Return the newly created todo record.
    return db_todo


# Register a GET endpoint that accepts a todo ID in the URL.
# Example: GET /todo/5
@router.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
def read_todo(todo_id: int,user: user_dependency, db: db_dependency):

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    # Search for the first todo whose ID matches todo_id.
    # first() returns the matching object or None if no record exists.
    todo = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.id).first()  # Filter by the authenticated user's ID

    # Check whether the requested todo was found.
    if not todo:

        # Stop processing and return HTTP 404 with an explanatory message.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found"
        )

    # Return the matching todo record.
    return todo


# Register a PUT endpoint to update an existing todo.
# Example: PUT /todo/5
@router.put("/todo/{todo_id}", status_code=status.HTTP_200_OK)
def update_todo(todo_id: int, todo: TodoRequest, user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    # Find the existing database record using its ID.
    db_todo = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.id).first()

    # If the record does not exist, return HTTP 404.
    if not db_todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found"
        )

    # Convert the validated request data into a dictionary.
    for key, value in todo.model_dump().items():

        # Update the matching attribute on the SQLAlchemy model object.
        # Example: setattr(db_todo, "title", "Learn Python")
        setattr(db_todo, key, value)

    # Save the changes to the database.
    db.commit()

    # Refresh the object to reflect its current database values.
    db.refresh(db_todo)

    # Return the updated todo record.
    return db_todo


# Register a DELETE endpoint to remove a todo by ID.
# Example: DELETE /todo/5
# Return HTTP 204 No Content when deletion succeeds.
@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int, user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    # Search for the todo record that should be deleted.
    db_todo = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.id).first()

    # If no matching record exists, return HTTP 404.
    if not db_todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found"
        )

    # Mark the selected database record for deletion.
    db.delete(db_todo)

    # Commit the transaction to permanently apply the deletion.
    db.commit()

    # Return no response body, as expected for HTTP 204.
    return None
