"""Application entry point: `uvicorn app.main:app --reload`.

The schema is managed by Alembic (`python -m scripts.migrate`), not created here.
"""
from fastapi import FastAPI, status

from app.core.config import settings
from app.core.constants import HEALTH_PATH, HEALTH_TAG, HEALTHY_STATUS
from app.routers import admin, auth, todos, users

app = FastAPI(title=settings.APP_NAME)


@app.get(HEALTH_PATH, status_code=status.HTTP_200_OK, tags=[HEALTH_TAG])
def health_check():
    return {"status": HEALTHY_STATUS}


app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(admin.router)
app.include_router(users.router)
