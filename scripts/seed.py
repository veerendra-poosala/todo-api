"""Fill the database with sample users and todos for manual API testing: `python -m scripts.seed`.

Seeding inserts *data*; migrations (`python -m scripts.migrate`) create the *tables*.
Run migrate first. The script is idempotent: running it again skips rows that already exist.

    python -m scripts.seed           # create missing users and their todos
    python -m scripts.seed --reset   # also wipe and recreate the seeded users' todos
"""
import argparse
import sys

from sqlalchemy import inspect

from app.core.config import settings
from app.core.constants import ROLE_ADMIN, ROLE_USER
from app.core.security import hash_password
from app.db.database import SessionLocal, engine
from app.db.models import Todos, Users

SEED_PASSWORD = "password123"

SEED_USERS = [
    {"username": "admin", "email": "admin@example.com", "first_name": "Ada", "last_name": "Admin",
     "role": ROLE_ADMIN, "phone_number": None},
    {"username": "alice", "email": "alice@example.com", "first_name": "Alice", "last_name": "Smith",
     "role": ROLE_USER, "phone_number": "5551234567"},
    {"username": "bob", "email": "bob@example.com", "first_name": "Bob", "last_name": "Jones",
     "role": ROLE_USER, "phone_number": None},
]

# (title, description, priority, complete) per username; priority is 1-3.
SEED_TODOS: dict[str, list[tuple[str, str, int, bool]]] = {
    "alice": [
        ("Buy groceries", "Milk, eggs, bread and coffee beans", 2, False),
        ("Finish FastAPI course", "Complete the authentication and testing sections", 3, False),
        ("Book dentist appointment", "Six-month checkup, morning slot preferred", 1, True),
        ("Pay electricity bill", "Due on the 15th, pay online", 3, True),
        ("Read a book", "Start reading Clean Architecture", 1, False),
        ("Plan weekend trip", "Look up hiking trails and weather forecast", 2, False),
        ("Clean the garage", "Sort old boxes and donate unused items", 1, True),
    ],
    "bob": [
        ("Fix bike tire", "Replace the inner tube on the rear wheel", 2, False),
        ("Write blog post", "Topic: lessons learned from building a REST API", 3, False),
        ("Call mom", "Weekly Sunday call", 3, True),
        ("Water the plants", "Balcony plants need water every two days", 1, False),
    ],
    "admin": [
        ("Review user reports", "Check flagged accounts and inactive users", 2, False),
    ],
}


def get_or_create_user(db, data: dict) -> tuple[Users, bool]:
    user = db.query(Users).filter(Users.username == data["username"]).first()
    if user is not None:
        return user, False
    user = Users(**data, hashed_password=hash_password(SEED_PASSWORD), is_active=True)
    db.add(user)
    db.flush()  # assigns user.id so todos can reference it
    return user, True


def seed_todos(db, user: Users, reset: bool) -> str:
    query = db.query(Todos).filter(Todos.owner_id == user.id)
    if reset:
        query.delete(synchronize_session=False)
    elif query.first() is not None:
        return "skipped (already has todos)"
    rows = SEED_TODOS.get(user.username, [])
    db.add_all(
        Todos(title=t, description=d, priority=p, complete=c, owner_id=user.id) for t, d, p, c in rows
    )
    return f"{len(rows)} todos {'reset' if reset else 'created'}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed sample users and todos.")
    parser.add_argument("--reset", action="store_true", help="Recreate todos for the seeded users")
    args = parser.parse_args()

    if settings.APP_ENV == "production":
        sys.exit("Refusing to seed: APP_ENV is 'production'.")
    if "users" not in inspect(engine).get_table_names():
        sys.exit("Tables not found. Run `python -m scripts.migrate` first.")

    with SessionLocal() as db:
        for data in SEED_USERS:
            user, created = get_or_create_user(db, data)
            todo_status = seed_todos(db, user, args.reset)
            print(f"{user.username:<6} ({user.role}) user {'created' if created else 'exists'}, {todo_status}")
        db.commit()

    print(f"\nLog in at /auth/token with any username above and password '{SEED_PASSWORD}'.")


if __name__ == "__main__":
    main()
