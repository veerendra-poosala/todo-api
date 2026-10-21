
# Import FastAPI to create the API application.
from fastapi import FastAPI

# Import the models module containing SQLAlchemy database models.
import models

# Import the database engine and session factory from database.py.
from database import engine
from routers import auth , todos, admin # Import the auth and todos routers for their respective endpoints.


# Create the FastAPI application instance.
app = FastAPI()

# Create database tables for registered models if they do not exist.
# The engine specifies which database SQLAlchemy should use.
models.Base.metadata.create_all(bind=engine)


app.include_router(auth.router)  # Include the auth router for authentication endpoints.
app.include_router(todos.router)  # Include the todos router for todo endpoints.
app.include_router(admin.router)  # Include the admin router for admin endpoints.

