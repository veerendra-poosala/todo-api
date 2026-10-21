from typing import Annotated
from fastapi import HTTPException, status, APIRouter, Depends
from pydantic import BaseModel
from passlib.context import CryptContext
from models import Users
from database import SessionLocal

router = APIRouter()

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str = "user"  # Default role is "user"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[SessionLocal, Depends(get_db)]


@router.post("/auth", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, request: CreateUserRequest):
    
    # Check if the username or email already exists
    existing_user = db.query(Users).filter((Users.username == request.username) | (Users.email == request.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )
    
    # Create a new user
    new_user = Users(
        username=request.username,
        email=request.email,
        first_name=request.first_name,
        last_name=request.last_name,
        hashed_password=bcrypt_context.hash(request.password),
        role=request.role,
        is_active=True  # Set the user as active by default
    )

    # Add the new user to the database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully", "user_id": new_user.id}