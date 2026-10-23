"""Application entry point: `uvicorn app.main:app --reload`."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, status

from app.core.config import settings
from app.core.constants import HEALTH_PATH, HEALTH_TAG, HEALTHY_STATUS
from app.db.mongo import init_db
from app.routers import admin, auth, todos, users


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Runs once at startup: connect to MongoDB and register the Beanie documents.
    client = await init_db(settings.MONGODB_URL, settings.MONGODB_DB)
    yield
    # Runs once at shutdown.
    await client.close()


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)


@app.get(HEALTH_PATH, status_code=status.HTTP_200_OK, tags=[HEALTH_TAG])
async def health_check():
    return {"status": HEALTHY_STATUS}


app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(admin.router)
app.include_router(users.router)
