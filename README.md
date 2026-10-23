# Todo API — FastAPI Learning Reference

A small but complete REST API built with **FastAPI**, **SQLAlchemy**, **Alembic**, **JWT auth** and **pytest**, packaged with **Docker**.

It is a learning and interview reference. Every section explains *what* a piece does and *why* it is used, so a developer new to FastAPI can read the code and understand the reasoning behind it.

---

## Table of contents

1. [What you'll learn](#1-what-youll-learn)
2. [Tech stack and why each package is used](#2-tech-stack-and-why-each-package-is-used)
3. [Project structure](#3-project-structure)
4. [How a request flows through the app](#4-how-a-request-flows-through-the-app)
5. [Quick start](#5-quick-start)
6. [API endpoints](#6-api-endpoints)
7. [Building APIs with FastAPI](#7-building-apis-with-fastapi)
8. [Configuration, `.env` and constants](#8-configuration-env-and-constants)
9. [Connecting to databases (SQLite, MySQL, PostgreSQL)](#9-connecting-to-databases-sqlite-mysql-postgresql)
10. [MongoDB with FastAPI](#10-mongodb-with-fastapi)
11. [Database migrations with Alembic](#11-database-migrations-with-alembic)
12. [Dependency injection](#12-dependency-injection)
13. [Authentication and authorization](#13-authentication-and-authorization)
14. [Testing with pytest](#14-testing-with-pytest)
15. [Docker](#15-docker)
16. [Deployment](#16-deployment)
17. [Sync vs async endpoints](#17-sync-vs-async-endpoints)
18. [Security best practices](#18-security-best-practices)
19. [Interview questions](#19-interview-questions)
20. [Troubleshooting](#20-troubleshooting)
21. [Next steps](#21-next-steps)

---

## 1. What you'll learn

- Building a REST API with FastAPI: routers, validation, status codes, response models
- Connecting FastAPI to **SQLite, MySQL, PostgreSQL** (SQLAlchemy) and **MongoDB** (Beanie)
- Managing schema changes with **Alembic migrations**
- **Dependency injection**: database sessions, the current user, role checks
- **JWT authentication** with hashed passwords, and role-based access
- **Unit and API tests** with pytest, including how to fake dependencies
- Configuration with **`.env` files**, and removing magic strings with a **constants file**
- **Dockerizing** the app and **deploying** it

### Branches

The same API is implemented on several branches so you can compare them:

| Branch | Database | What's different |
|---|---|---|
| `main` / `pytest` | **MySQL** | The reference implementation (this README) |
| `sqlite` | **SQLite** | No server needed; file-based DB; batch-mode migrations |
| `postgresql` | **PostgreSQL** | `psycopg2` driver; Postgres container in Docker |
| `mongodb` | **MongoDB** | No SQLAlchemy/Alembic; async **Beanie** ODM on **Motor** |

```bash
git checkout postgresql   # switch to another implementation
```

---

## 2. Tech stack and why each package is used

| Package | What it does | Why this project uses it |
|---|---|---|
| `fastapi` | Web framework for building APIs | Fast, type-hint driven, validates requests and generates Swagger docs automatically |
| `uvicorn[standard]` | ASGI server | Runs the FastAPI app. `[standard]` adds faster event-loop and HTTP libraries |
| `gunicorn` | Process manager | Runs several Uvicorn worker processes in production |
| `python-multipart` | Form-data parser | Required by `OAuth2PasswordRequestForm` for the `/auth/token` login form |
| `pydantic-settings` | Settings from env vars / `.env` | Typed, validated config. The app refuses to start if a required setting is missing |
| `email-validator` | Email validation | Enables Pydantic's `EmailStr` type on sign-up |
| `SQLAlchemy` | ORM + SQL toolkit | Work with tables as Python classes. The same code runs on SQLite, MySQL and PostgreSQL |
| `alembic` | Migration tool | Versioned, repeatable schema changes (from the same author as SQLAlchemy) |
| `PyMySQL` | MySQL driver | Pure-Python driver SQLAlchemy uses to talk to MySQL (`mysql+pymysql://`) |
| `cryptography` | Crypto primitives | Needed by PyMySQL for MySQL 8's default `caching_sha2_password` authentication |
| `psycopg2-binary` | PostgreSQL driver | Driver for `postgresql+psycopg2://` URLs |
| `passlib` + `bcrypt` | Password hashing | Stores a slow, salted bcrypt hash instead of the password itself |
| `python-jose` | JWT encode/decode | Creates and verifies the access tokens |
| `pytest` | Test runner | Fixtures, plain `assert`, auto-discovery |
| `httpx` | HTTP client | Used under the hood by FastAPI's `TestClient` |

**Database drivers at a glance**

| Database | Driver package | SQLAlchemy URL prefix |
|---|---|---|
| SQLite | built into Python (`sqlite3`) | `sqlite:///` |
| MySQL | `PyMySQL` (+ `cryptography`) | `mysql+pymysql://` |
| PostgreSQL | `psycopg2-binary` (or `psycopg[binary]` v3) | `postgresql+psycopg2://` |
| MongoDB | `motor` + `beanie` (no SQLAlchemy) | `mongodb://` |

---

## 3. Project structure

```
TodoApp/
├── app/
│   ├── main.py              # Creates the FastAPI app, registers routers, /health
│   ├── dependencies.py      # Shared dependencies: get_db, get_current_user, get_current_admin
│   ├── core/
│   │   ├── config.py        # Settings loaded from .env (pydantic-settings)
│   │   ├── constants.py     # All magic strings and numbers in one place
│   │   └── security.py      # Password hashing and JWT helpers
│   ├── db/
│   │   ├── database.py      # Engine, SessionLocal, Base
│   │   └── models.py        # ORM models: Users, Todos
│   ├── schemas/             # Pydantic request/response models (the API contract)
│   │   ├── auth.py
│   │   ├── todo.py
│   │   └── user.py
│   └── routers/             # One file per feature, each an APIRouter
│       ├── auth.py
│       ├── todos.py
│       ├── admin.py
│       └── users.py
├── alembic/                 # Migration environment and versions/
├── alembic.ini
├── scripts/migrate.py       # Bootstraps a new DB or applies pending migrations
├── tests/                   # pytest suite (conftest.py holds shared fixtures)
├── .env.example             # Template for your local .env
├── Dockerfile
├── docker-compose.yml       # API + MySQL
├── pytest.ini
└── requirements.txt
```

**Why this layering?** Each folder has one job:

| Layer | Responsibility | Should NOT |
|---|---|---|
| `routers/` | HTTP: paths, status codes, calling the DB | Hold config or reusable security logic |
| `schemas/` | Shape and validation of API input/output | Know about the database |
| `db/models.py` | Shape of database tables | Know about HTTP |
| `dependencies.py` | Building shared objects per request | Contain business rules for a single route |
| `core/` | Config, constants, security helpers | Import from routers |

Keeping **schemas** (Pydantic) separate from **models** (SQLAlchemy) means the API can change shape without changing the table, and private columns such as `hashed_password` are never exposed by accident.

---

## 4. How a request flows through the app

```
Client
  │  POST /todos  {"title": "...", ...}   Authorization: Bearer <jwt>
  ▼
Uvicorn (ASGI server)
  ▼
FastAPI routing ──► app/routers/todos.py :: create_todo
  ▼
Dependencies resolved (app/dependencies.py)
  ├─ get_db()            → opens a SQLAlchemy Session
  └─ get_current_user()  → reads the JWT, loads the user (401 if invalid)
  ▼
Body validated by Pydantic (TodoRequest) → 422 if invalid
  ▼
Route function runs: creates Todos(...), db.commit()
  ▼
Return value filtered through response_model (TodoResponse) → JSON
  ▼
get_db() cleanup closes the session
```

---

## 5. Quick start

**Prerequisites:** Python 3.11+ and a running MySQL server. You can also use Docker (see [Docker](#15-docker)) or the `sqlite` branch, which needs no database server.

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env               # then edit DATABASE_URL and SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"   # generate a SECRET_KEY

# 4. Create the database in MySQL (once)
#    CREATE DATABASE todoapplication;

# 5. Create or upgrade the schema
python -m scripts.migrate

# 6. Run the server (auto-reloads on code changes)
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000/docs** for the interactive Swagger UI, or `/redoc` for ReDoc.

**Try it in Swagger:** `POST /auth/user` to sign up → click **Authorize** and log in → call any `/todos` endpoint.

---

## 6. API endpoints

| Method | Path | Auth | Description | Success |
|---|---|---|---|---|
| GET | `/health` | — | Health check | 200 |
| POST | `/auth/user` | — | Register a user | 201 |
| POST | `/auth/token` | — | Log in (form data) and get a JWT | 200 |
| GET | `/todos` | User | List your todos | 200 |
| POST | `/todos` | User | Create a todo | 201 |
| GET | `/todos/{todo_id}` | User | Get one of your todos | 200 |
| PUT | `/todos/{todo_id}` | User | Update one of your todos | 200 |
| DELETE | `/todos/{todo_id}` | User | Delete one of your todos | 204 |
| GET | `/admin/todo` | Admin | List every user's todos | 200 |
| DELETE | `/admin/todo/{todo_id}` | Admin | Delete any todo | 204 |
| GET | `/user/get-user-details` | User | Your profile (no password hash) | 200 |
| PUT | `/user/change-password` | User | `{current_password, new_password}` | 200 |
| PUT | `/user/update-phone-number` | User | `{phone_number}` | 200 |

**Common error codes:** `400` business rule failed · `401` missing or invalid token · `403` logged in but not allowed · `404` not found (or not yours) · `422` request failed validation.

**Example with curl:**

```bash
curl -X POST localhost:8000/auth/user -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","first_name":"Alice","last_name":"A","password":"secret123"}'

TOKEN=$(curl -s -X POST localhost:8000/auth/token -d "username=alice&password=secret123" | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

curl -X POST localhost:8000/todos -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"Learn FastAPI","description":"Read the README","priority":1}'
```

---

## 7. Building APIs with FastAPI

### Routers

`APIRouter` groups related endpoints. `main.py` registers each router with `include_router`.

```python
router = APIRouter(prefix=TODOS_PREFIX, tags=[TODOS_TAG])   # app/routers/todos.py

@router.get("/{todo_id}", response_model=TodoResponse)
def read_todo(user: CurrentUser, db: DbSession, todo_id: int = Path(gt=0)):
    return get_owned_todo_or_404(db, todo_id, user)
```

### Where parameters come from

| Declared as | FastAPI reads it from | Example |
|---|---|---|
| A name inside `{}` in the path | URL path | `todo_id: int = Path(gt=0)` |
| Simple type not in the path | Query string | `?skip=0&limit=10` → `skip: int = 0` |
| A Pydantic model | JSON body | `todo: TodoRequest` |
| `Depends(...)` | A dependency | `db: DbSession` |
| `OAuth2PasswordRequestForm` | Form data | Login endpoint |

### Validation with Pydantic

```python
class TodoRequest(BaseModel):                     # app/schemas/todo.py
    title: str = Field(min_length=3, max_length=100)
    priority: int = Field(ge=1, le=3)
    complete: bool = False
```

If a request breaks these rules, FastAPI returns **422** with details before your code runs.

### Response models

`response_model=TodoResponse` controls what is returned. It filters out any field not listed, and `from_attributes=True` lets Pydantic read SQLAlchemy objects. This is how `/user/get-user-details` avoids leaking `hashed_password`.

### Status codes and errors

- Set the success code on the decorator: `status_code=status.HTTP_201_CREATED`.
- Raise `HTTPException(status_code=404, detail=...)` to stop and return an error.
- Use `status.HTTP_...` constants instead of bare numbers.

---

## 8. Configuration, `.env` and constants

### Settings (`app/core/config.py`)

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    DATABASE_URL: str          # required — no default
    SECRET_KEY: str            # required — no default
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 20
```

- **Priority:** real environment variables > `.env` file > defaults.
- **Why:** the same code runs locally, in Docker and in production. Only the environment changes ([12-factor app](https://12factor.net/config)).
- **Required fields have no default**, so a missing secret stops the app at startup instead of failing later.
- `.env` is **gitignored**. Commit `.env.example` with placeholder values only.

### Constants (`app/core/constants.py`)

Route prefixes, role names, JWT claim keys, validation limits and error messages are all defined once:

```python
ROLE_ADMIN = "admin"
TODO_NOT_FOUND = "Todo with id {todo_id} not found"
```

**Why:** a typo in `"admni"` silently breaks an admin check. A typo in `ROLE_ADMNI` is an import error. Constants are also easy to find and change in one place, and tests assert against the same values the code uses.

**Settings vs constants:** if a value changes **between environments** (URLs, secrets, timeouts), it belongs in settings. If it is fixed **for the code** (role names, messages), it is a constant.

---

## 9. Connecting to databases (SQLite, MySQL, PostgreSQL)

### The three SQLAlchemy building blocks (`app/db/database.py`)

```python
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

| Object | What it is |
|---|---|
| `engine` | Knows how to connect and keeps a **connection pool** |
| `SessionLocal` | Factory for `Session` objects. A session is a unit of work: you add, query and commit through it |
| `Base` | Parent class for models. `Base.metadata` describes every table |

### Switching databases = changing one URL

```
dialect+driver://username:password@host:port/database
```

| Database | `DATABASE_URL` example | Notes |
|---|---|---|
| SQLite | `sqlite:///./todosapp.db` | File-based, zero setup. Needs `check_same_thread=False` (handled in `database.py`) |
| MySQL | `mysql+pymysql://root:root@localhost:3306/todoapplication` | Create the database first. Needs `cryptography` for MySQL 8 auth |
| PostgreSQL | `postgresql+psycopg2://postgres:postgres@localhost:5432/todoapplication` | Create the database first |

Special characters in passwords must be URL-encoded (`@` → `%40`).

### Models (`app/db/models.py`)

```python
class Todos(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
```

### Choosing a database

| | SQLite | MySQL | PostgreSQL |
|---|---|---|---|
| Setup | None (a file) | Server | Server |
| Concurrency | One writer at a time | Good | Excellent |
| Best for | Prototypes, tests, small apps | Web apps, wide hosting support | Complex queries, JSON, strict correctness |

---

## 10. MongoDB with FastAPI

MongoDB is a **document database**: it stores JSON-like documents and has no fixed table schema. SQLAlchemy and Alembic only work with SQL databases, so the **`mongodb` branch** replaces them:

| SQL version | MongoDB version |
|---|---|
| SQLAlchemy models | **Beanie** `Document` classes (Pydantic-based ODM) |
| `PyMySQL` / `psycopg2` driver | **Motor** (async MongoDB driver) |
| `Session` per request via `get_db` | `init_beanie()` once at startup (FastAPI `lifespan`) |
| Integer ids | `ObjectId` (`PydanticObjectId`) |
| Alembic migrations | None for structure. Data changes are done with scripts |

```python
# Sketch — see the mongodb branch for the full code
class Todo(Document):
    title: str
    owner_id: PydanticObjectId
    class Settings:
        name = "todos"

@asynccontextmanager
async def lifespan(app):
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    await init_beanie(database=client[settings.MONGODB_DB], document_models=[User, Todo])
    yield
```

**SQL or MongoDB?** Use SQL when data is relational and needs joins and transactions (users ↔ todos). Use MongoDB when the shape of documents varies, or when you read and write whole documents at once.

---

## 11. Database migrations with Alembic

### What is a migration, and why use one?

A migration is a **versioned script that changes the database schema**, for example adding a column. Migrations matter because:

- The schema is **version-controlled** together with the code.
- Every environment (your laptop, a teammate's, staging, production) gets the **same changes in the same order**.
- **Existing data is kept**. Dropping and recreating tables would lose it.
- Changes can be **rolled back** (`downgrade`).

`Base.metadata.create_all()` only creates tables that are **missing**. It never alters an existing table, so it can't add the `phone_number` column to a live database. That's what Alembic is for.

### How this project is set up

- `alembic/env.py` imports `app.db.models` (for autogenerate) and reads `DATABASE_URL` from settings. The URL is never hardcoded in `alembic.ini`.
- `alembic/versions/9f3ba22ed85b_...py` adds `users.phone_number`.
- `scripts/migrate.py`: on a **brand-new** DB it creates all tables and **stamps** them as current. Otherwise it runs `alembic upgrade head`.

### Everyday commands

```bash
alembic revision --autogenerate -m "add due_date to todos"   # 1. change models.py, then generate
# 2. ALWAYS read the generated file in alembic/versions/ before applying it
alembic upgrade head          # apply all pending migrations
alembic downgrade -1          # undo the last migration
alembic current               # which revision is the DB at?
alembic history               # list all revisions
alembic stamp head            # mark the DB as up to date without running anything
```

A migration file has two functions:

```python
def upgrade():   op.add_column("users", sa.Column("phone_number", sa.String(20), nullable=True))
def downgrade(): op.drop_column("users", "phone_number")
```

**Autogenerate can't detect everything**, for example column renames (it sees them as drop + add, which loses data). Always review the generated file. On **SQLite**, `ALTER TABLE` is limited, so the `sqlite` branch uses `render_as_batch=True`.

---

## 12. Dependency injection

**Dependency injection (DI):** a function **declares what it needs** and FastAPI **creates it and passes it in**. The function never builds those objects itself.

```python
# app/dependencies.py
def get_db():
    db = SessionLocal()
    try:
        yield db          # value injected into the route
    finally:
        db.close()        # runs after the response, even if an error occurred

DbSession = Annotated[Session, Depends(get_db)]       # reusable alias
CurrentUser = Annotated[Users, Depends(get_current_user)]
AdminUser = Annotated[Users, Depends(get_current_admin)]

# a route just asks for them
@router.get("")
def read_all(user: CurrentUser, db: DbSession): ...
```

### How it helps

| Benefit | In this project |
|---|---|
| **No repetition** | Session handling and token checking are written once and used by every route |
| **Guaranteed cleanup** | `yield` dependencies close the DB session even when the route raises |
| **Composition** | `get_current_admin` depends on `get_current_user`, which depends on `get_db` and the OAuth2 token |
| **Testability** | Tests replace real dependencies with `app.dependency_overrides` (see [Testing](#14-testing-with-pytest)) |
| **Per-request caching** | If two dependencies both need `get_db`, the same session is shared within one request |

**Security as a dependency:** admin routes take `_admin: AdminUser`. A route can't forget the role check, because the dependency runs before the route does.

---

## 13. Authentication and authorization

**Authentication** = *who are you?* **Authorization** = *what are you allowed to do?*

### Password storage

```python
pwd_context = CryptContext(schemes=["bcrypt"])   # app/core/security.py
hash_password("secret123")   # → "$2b$12$..." (salted, slow by design)
verify_password("secret123", stored_hash)
```

Passwords are never stored or logged. bcrypt is **slow on purpose** and **salted**, which defeats brute force and rainbow tables.

### OAuth2 password flow with JWT

1. `POST /auth/token` with form fields `username` and `password`.
2. The server checks the bcrypt hash and returns `{"access_token": "<jwt>", "token_type": "bearer"}`.
3. The client sends `Authorization: Bearer <jwt>` on later requests.
4. `get_current_user` decodes the token, checks its signature and expiry, and loads the user.

### What's inside a JWT

`header.payload.signature`, each part base64-encoded:

```json
{ "sub": "alice", "user_id": 1, "role": "user", "exp": 1767225600 }
```

The payload can be **read by anyone**. It is signed, not encrypted, so never put secrets in it. The signature (HS256 with `SECRET_KEY`) proves the token wasn't changed.

### Roles

`get_current_admin` returns **403 Forbidden** if `user.role != ROLE_ADMIN`. **401** means "not authenticated". **403** means "authenticated, but not allowed".

---

## 14. Testing with pytest

### Why test?

Tests catch regressions, document how the API should behave, and make refactoring safe. This repo's restructure was checked by the test suite.

### Run the tests

```bash
pytest                    # all tests (testpaths = tests in pytest.ini)
pytest -v                 # verbose
pytest tests/test_todos.py::test_create_todo   # a single test
pytest -k "auth"          # tests whose name matches
pip install pytest-cov && pytest --cov=app     # coverage report
```

### How the test setup works

| Piece | File | Purpose |
|---|---|---|
| Test settings | `tests/conftest.py` (top) | Sets `DATABASE_URL` to SQLite **before** importing the app, so tests never touch the real DB |
| Test database | `tests/utils.py` | Separate `test.db` engine + `TestingSessionLocal`; tables created from models |
| `TestClient` | `tests/utils.py` | Calls the app in-process. No server needed |
| Dependency overrides | `tests/conftest.py` | `get_db` → test session; `get_current_user` → a known test user |
| Fixtures | `tests/conftest.py` | `test_user` (autouse) and `test_todo` insert data and clean up after each test |

```python
# Overriding dependencies — DI makes this possible
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

@pytest.fixture
def test_todo(test_user):              # fixtures can depend on other fixtures
    ...
    yield todo                          # code after yield = teardown

def test_read_one_authenticated(test_todo):        # pytest injects the fixture by name
    response = client.get(f"/todos/{test_todo.id}")
    assert response.status_code == status.HTTP_200_OK
```

### What to test (examples in this repo)

- **Happy paths:** create, read, update, delete.
- **Errors:** 404 for a missing todo, 422 for invalid input, 400 for a duplicate user, 403 for a non-admin.
- **Unit tests on functions:** `authenticate_user`, `create_access_token`, `get_current_user` (valid, expired, garbage and incomplete tokens).
- **Side effects:** check the database after the request, not just the response.

**Good test habits:** each test is independent (data is reset per test), uses **AAA** (Arrange, Act, Assert), and asserts against constants rather than copied strings.

---

## 15. Docker

### Why Docker?

"Works on my machine" goes away. The image contains the exact Python version, dependencies and code. `docker compose` starts the API **and** MySQL with one command.

### Dockerfile walkthrough

```dockerfile
FROM python:3.13-slim                         # small official base image
WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt   # cached layer: only rebuilt when requirements change
COPY . .                                      # code copied after deps, so code edits rebuild fast
RUN useradd --create-home appuser && chown -R appuser /code
USER appuser                                  # don't run as root
CMD ["sh", "-c", "python -m scripts.migrate && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

`--host 0.0.0.0` is required inside a container. `127.0.0.1` would only accept connections from inside the container itself. `.dockerignore` keeps `.env`, `.git`, tests and local DB files out of the image.

### docker-compose

- `db`: `mysql:8.4` with a **healthcheck** and a named **volume**, so data survives restarts.
- `api`: built from the Dockerfile. It reads `.env` and overrides `DATABASE_URL` to point at host **`db`** (the service name), and it waits until MySQL is healthy.

```bash
cp .env.example .env              # once
docker compose up --build         # build and start → http://localhost:8000/docs
docker compose logs -f api        # follow API logs
docker compose exec api alembic current
docker compose down               # stop
docker compose down -v            # stop AND delete the database volume
```

MySQL is exposed on host port **3307** so it doesn't clash with a local MySQL on 3306.

---

## 16. Deployment

### Production checklist

- [ ] `SECRET_KEY` is a long random value from the platform's secret store, not from git
- [ ] `DATABASE_URL` points to a managed database (RDS, Cloud SQL, Railway, etc.)
- [ ] Migrations run **before** the new code starts serving (`python -m scripts.migrate` or `alembic upgrade head`)
- [ ] Multiple worker processes are running
- [ ] HTTPS is in front of the app (a reverse proxy or the platform's load balancer)
- [ ] `/health` is wired to the platform's health checks
- [ ] Logs go to stdout and are collected by the platform

### Running with multiple workers

```bash
gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000
# or simply
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

A common starting point is `(2 × CPU cores) + 1` workers.

### Option A — Platform as a Service (Render, Railway, Fly.io)

1. Push the repo to GitHub.
2. Create a new service from the repo. The platform detects the `Dockerfile`.
3. Add a managed MySQL or PostgreSQL database and set `DATABASE_URL` and `SECRET_KEY` as environment variables.
4. Set the health check path to `/health` and deploy. The container's `CMD` runs migrations on start.

### Option B — Virtual machine (AWS EC2, DigitalOcean)

```bash
# on the server
sudo apt install docker.io docker-compose-plugin nginx certbot python3-certbot-nginx
git clone <repo> && cd TodoApp && cp .env.example .env   # set real secrets
docker compose up -d --build
```

Put **Nginx** in front as a reverse proxy, and use **Certbot** for HTTPS:

```nginx
server {
    server_name api.example.com;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo certbot --nginx -d api.example.com
```

### CI/CD idea

On every push: install requirements → run `pytest` → build the Docker image → deploy if tests pass (for example with GitHub Actions).

---

## 17. Sync vs async endpoints

| | `def` endpoint | `async def` endpoint |
|---|---|---|
| Runs in | A thread pool | The event loop |
| Use when | Calling **blocking** libraries (SQLAlchemy sync sessions, `requests`) | Every I/O call is awaitable (`httpx.AsyncClient`, Motor, async SQLAlchemy) |
| Danger | — | A blocking call inside `async def` freezes **every** request |

The SQL branches use **sync** SQLAlchemy, so their routes are plain `def`. The `mongodb` branch uses Motor, which is async, so its routes are `async def`.

---

## 18. Security best practices

- Hash passwords with bcrypt and never log them.
- Keep secrets in environment variables, **never in git**. If a secret leaks, rotate it.
- Short-lived access tokens (`ACCESS_TOKEN_EXPIRE_MINUTES`). Add refresh tokens for long sessions.
- Validate every input with Pydantic, and filter every output with `response_model`.
- Return **404** for other users' resources, so you don't reveal that they exist.
- Use the ORM or bound parameters. **Never** build SQL with f-strings (SQL injection).
- Enable CORS only for the origins you trust (`fastapi.middleware.cors.CORSMiddleware`).
- Run containers as a non-root user, and keep dependencies updated.
- Add rate limiting on `/auth/token` to slow down brute-force attacks.

---

## 19. Interview questions

<details>
<summary><b>FastAPI basics</b></summary>

1. **What is FastAPI and why is it fast?**
   A Python web framework built on **Starlette** (ASGI) and **Pydantic**. It is fast at runtime because it's async and ASGI-based, and fast to develop with because type hints drive validation and docs.

2. **What is ASGI vs WSGI?**
   WSGI (Flask, Django classic) is synchronous: one request per worker thread. ASGI supports async, WebSockets and long-lived connections. Uvicorn is an ASGI server.

3. **How does FastAPI generate Swagger docs?**
   From path operations, type hints and Pydantic models, it builds an **OpenAPI** schema at `/openapi.json`. Swagger UI (`/docs`) and ReDoc (`/redoc`) render it.

4. **Path vs query vs body parameters?**
   Path: part of the URL template (`/todos/{id}`). Query: simple types not in the path (`?limit=10`). Body: Pydantic models.

5. **What does a 422 mean?**
   The request failed Pydantic validation. FastAPI returns it automatically, with details of which field failed.

6. **What is `response_model` for?**
   It validates and **filters** the output, documents it in OpenAPI, and stops sensitive fields such as `hashed_password` from leaking.

7. **APIRouter — why?**
   It splits endpoints into modules with a shared prefix, tags and dependencies, which keeps `main.py` small.
</details>

<details>
<summary><b>Dependency injection</b></summary>

8. **What is dependency injection in FastAPI?**
   Declaring needed resources with `Depends()`. FastAPI resolves them per request, including nested dependencies, and injects them into the route.

9. **Why use `yield` in a dependency?**
   Code before `yield` is setup and code after it is teardown. Teardown runs after the response, even on errors. That makes it ideal for DB sessions.

10. **How do you mock a dependency in tests?**
    `app.dependency_overrides[real_dep] = fake_dep`.

11. **Are dependencies cached?**
    Yes, within a single request. The same dependency used twice is called once, unless you pass `use_cache=False`.
</details>

<details>
<summary><b>Databases and migrations</b></summary>

12. **What is an ORM? Pros and cons?**
    It maps classes to tables and objects to rows. Pros: portable across databases, safe parameterized queries, less boilerplate. Cons: can hide inefficient queries (N+1 problem), and it's an extra layer to learn.

13. **Engine vs Session in SQLAlchemy?**
    The engine owns the connection pool and is created once. A session is a short-lived unit of work, created per request.

14. **Why one session per request?**
    It isolates transactions between requests, makes it clear when to commit or roll back, and returns the connection to the pool afterwards.

15. **What are migrations and why not just `create_all`?**
    Versioned schema changes that keep existing data. `create_all` only creates missing tables. It can't alter or drop columns.

16. **What does `alembic upgrade head` do?**
    It applies every migration between the DB's current revision (stored in the `alembic_version` table) and the latest one.

17. **SQL vs NoSQL — when would you choose MongoDB?**
    MongoDB fits flexible or nested documents and whole-document reads and writes. SQL fits relational data, joins and strong consistency.

18. **What is the N+1 query problem?**
    One query fetches N parents, then N more queries fetch their children. Fix it with eager loading (`joinedload`, `selectinload`).
</details>

<details>
<summary><b>Security</b></summary>

19. **Authentication vs authorization?**
    Authentication: who you are (login, token). Authorization: what you may do (roles, ownership).

20. **401 vs 403?**
    401: not authenticated, or the token is invalid. 403: authenticated, but not permitted.

21. **How does JWT work? Is it encrypted?**
    `header.payload.signature`. The payload is only **base64-encoded**, so anyone can read it. The signature stops tampering. It is not encryption.

22. **Why bcrypt instead of SHA-256 for passwords?**
    bcrypt is deliberately slow and salted, with a tunable cost. Fast hashes such as SHA-256 can be brute-forced quickly.

23. **How do you log out with stateless JWTs?**
    Use short expiry plus refresh tokens. Revoke by keeping a deny-list of token ids (`jti`), or by rotating keys.
</details>

<details>
<summary><b>Testing, config and deployment</b></summary>

24. **What is a pytest fixture?**
    A reusable setup/teardown function injected by name into tests. Code after `yield` is the teardown. Its scope can be function, module or session.

25. **What is `conftest.py`?**
    A file pytest loads automatically. Fixtures defined there are available to every test in that directory, with no import needed.

26. **Unit vs integration test?**
    A unit test checks one function in isolation (`create_access_token`). An integration test checks components together (HTTP → route → DB via `TestClient`).

27. **Why environment variables for config?**
    The same build runs in every environment, and secrets stay out of the code (12-factor). pydantic-settings adds types and validation.

28. **Why Gunicorn with Uvicorn workers?**
    Gunicorn manages several processes (using multiple CPU cores, restarting crashed workers). Each Uvicorn worker runs the async event loop.

29. **What does `0.0.0.0` mean in Docker?**
    Listen on all network interfaces, so traffic from outside the container (port mapping) can reach the app.

30. **How do you run migrations in a deployment?**
    As a step before the new version starts serving: a release command, init container or entrypoint. Migrations should be backward-compatible, so old and new code can run at the same time during a rollout.
</details>

---

## 20. Troubleshooting

| Problem | Fix |
|---|---|
| `ValidationError: DATABASE_URL / SECRET_KEY field required` | Create `.env` from `.env.example` and run from the `TodoApp/` folder |
| `(2003) Can't connect to MySQL server` | Start MySQL, or use `docker compose up db` and `localhost:3307` |
| `Unknown database 'todoapplication'` | `CREATE DATABASE todoapplication;` |
| `RuntimeError: 'cryptography' package is required` | `pip install cryptography` (MySQL 8 auth) |
| `(trapped) error reading bcrypt version` or `ValueError: password cannot be longer than 72 bytes` | Keep `bcrypt==4.0.1`. Newer bcrypt releases are incompatible with the unmaintained `passlib` |
| `ModuleNotFoundError: No module named 'app'` | Run commands from the `TodoApp/` directory |
| `422 Unprocessable Entity` | Read `detail` in the response. It names the invalid field |
| `401` in Swagger | Click **Authorize** and log in first |
| Alembic `Target database is not up to date` | `alembic upgrade head` before `alembic revision --autogenerate` |

---

## 21. Next steps

- Pagination and filtering on `GET /todos` (`skip`, `limit`, `complete`)
- Refresh tokens and logout
- Async SQLAlchemy (`create_async_engine` + `asyncpg`)
- A service/repository layer between routers and the DB
- GitHub Actions CI running `pytest` on every push
- Structured logging and request IDs
- Rate limiting and CORS configuration
