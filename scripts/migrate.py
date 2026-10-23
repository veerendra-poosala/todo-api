"""Bring the database schema up to date: `python -m scripts.migrate`.

- Brand-new database (no `alembic_version` table): create every table from the models,
  then stamp it with the latest revision so Alembic knows it is current.
- Existing database: apply any pending Alembic migrations.

The bootstrap step exists because this project's first migration only adds a column;
the original tables were created before Alembic was introduced.
"""
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.db import models  # noqa: F401 - registers models on Base.metadata
from app.db.database import Base, engine

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"
ALEMBIC_VERSION_TABLE = "alembic_version"


def main() -> None:
    config = Config(str(ALEMBIC_INI))
    if ALEMBIC_VERSION_TABLE not in inspect(engine).get_table_names():
        Base.metadata.create_all(bind=engine)
        command.stamp(config, "head")
    else:
        command.upgrade(config, "head")


if __name__ == "__main__":
    main()
