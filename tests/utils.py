from pymongo import MongoClient
from pymongo.errors import PyMongoError

TEST_MONGODB_DB = "todoapp_test"  # Separate throwaway database, never the real one
TEST_USER_PASSWORD = "testpassword"


def mongo_is_available(url: str) -> bool:
    try:
        with MongoClient(url, serverSelectionTimeoutMS=2000) as client:
            client.admin.command("ping")
        return True
    except PyMongoError:
        return False
