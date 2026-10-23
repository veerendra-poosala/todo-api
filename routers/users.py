
# Import HTTPException to return HTTP errors, such as 404 Not Found.
# Import status constants, such as 200, 201, 204, and 404.
# Import Depends to inject dependencies, such as a database session.
from passlib.context import CryptContext
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
from models import Users

# Import the database engine and session factory from database.py.
from database import engine, SessionLocal
from routers import auth  # Import the auth router for authentication endpoints.

from .auth import get_current_user  # Import the get_current_user function for user authentication.

# Create the FastAPI application instance.
router = APIRouter(
    prefix = "/user",
    tags = ["user"]
)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)


class PhoneNumberRequest(BaseModel):
    phone_number: str = Field(..., min_length=10, max_length=20)



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
user_dependency = Annotated[Users, Depends(get_current_user)]  # Dependency for authenticated user
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



@router.get("/get-user-details", status_code=status.HTTP_200_OK)
async def get_user(db: db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed")
    user_data = db.query(Users).filter(Users.id == user.id).first()
    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user_data


@router.put("/change-password", status_code=status.HTTP_200_OK)
async def change_password(request: ChangePasswordRequest, db: db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed")
    user_data = db.query(Users).filter(Users.id == user.id).first()
    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not bcrypt_context.verify(request.current_password, user_data.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect current password")
    if request.new_password == request.current_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must differ from current password")
    user_data.hashed_password = bcrypt_context.hash(request.new_password)
    db.commit()
    return {"message": "Password changed successfully"}


@router.put("/update-phone-number", status_code=status.HTTP_200_OK)
async def update_phone_number(request: PhoneNumberRequest,db: db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed")
    user_data = db.query(Users).filter(Users.id == user.id).first()
    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user_data.phone_number = request.phone_number
    db.commit()
    return {"message": "Phone number updated successfully"}