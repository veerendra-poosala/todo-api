"""MongoDB connection and Beanie (ODM) initialisation.

Unlike SQLAlchemy there is no per-request session: one client (with its own connection
pool) is created at startup and Beanie binds every Document class to the database.
"""
from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.db.models import DOCUMENT_MODELS


async def init_db(mongodb_url: str, db_name: str) -> AsyncMongoClient:
    client = AsyncMongoClient(mongodb_url)
    # init_beanie also creates the indexes declared on the models (e.g. unique username).
    await init_beanie(database=client[db_name], document_models=DOCUMENT_MODELS)
    return client
