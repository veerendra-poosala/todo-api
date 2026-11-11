# Todo API on SQL Server: Step-by-Step Guide

From a fresh machine to a running API, first locally and then in Docker, and finally deployed.
Every step has copy-paste commands. **PowerShell** (Windows) is shown first; **bash** (macOS/Linux) follows where it differs.

> Branch: `mssql` · Stack: FastAPI · SQLAlchemy 2 · Alembic · pyodbc · ODBC Driver 18 · SQL Server 2019+

---

## Contents

0. [Prerequisites](#0-prerequisites)
1. [Prepare SQL Server](#1-prepare-sql-server)
2. [Get the code](#2-get-the-code)
3. [Virtual environment and dependencies](#3-virtual-environment-and-dependencies)
4. [Configure `.env`](#4-configure-env)
5. [Test the database connection](#5-test-the-database-connection)
6. [Migrations (create and evolve the schema)](#6-migrations)
7. [Run the API](#7-run-the-api)
8. [Run the tests](#8-run-the-tests)
9. [Run everything in Docker (local)](#9-run-everything-in-docker-local)
10. [Deploy with Docker](#10-deploy-with-docker)
11. [Troubleshooting](#11-troubleshooting)
12. [Command cheat sheet](#12-command-cheat-sheet)

---

## 0. Prerequisites

| Tool | Why | Check it |
|---|---|---|
| Python 3.11+ | Runs the app | `python --version` |
| SQL Server 2019+ (Developer or Express edition) | The database | `Get-Service MSSQLSERVER` (should be *Running*) |
| SSMS or Azure Data Studio | GUI to inspect data | open it |
| **ODBC Driver 18 for SQL Server** | `pyodbc` is only a bridge; this is the real driver | `Get-OdbcDriver \| ? Name -like "*SQL Server*"` |
| Git | Get the code | `git --version` |
| Docker Desktop (for steps 9–10) | Containers | `docker --version` |

Download links:
- SQL Server Developer: https://www.microsoft.com/sql-server/sql-server-downloads
- ODBC Driver 18: https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server
- macOS: `brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release && brew install msodbcsql18`

---

## 1. Prepare SQL Server

Do this once per machine.

### 1.1 Enable SQL Server authentication (mixed mode)
The app logs in with a username and password, not Windows auth.
SSMS → right-click the server → **Properties → Security** → *SQL Server and Windows Authentication mode* → OK → **restart the service**:

```powershell
Restart-Service MSSQLSERVER   # run PowerShell as Administrator
```

### 1.2 Enable TCP/IP on port 1433
**SQL Server Configuration Manager** → *SQL Server Network Configuration* → *Protocols for MSSQLSERVER* → **TCP/IP = Enabled** → restart the service.

```powershell
Get-NetTCPConnection -State Listen -LocalPort 1433   # should list a listener
```

### 1.3 Create a login and the database
In SSMS, connect as an admin, open **New Query** and run:

```sql
-- Skip CREATE LOGIN if your login (e.g. dev_admin) already exists
CREATE LOGIN dev_admin WITH PASSWORD = '<A_STRONG_PASSWORD>';

CREATE DATABASE todoapplication;
GO

USE todoapplication;
CREATE USER dev_admin FOR LOGIN dev_admin;
ALTER ROLE db_owner ADD MEMBER dev_admin;   -- needed so migrations can create/alter tables
```

> **Why a database first?** Unlike SQLite, SQL Server won't create a database for you when you connect. Migrations create the *tables*, but the *database* must already exist.

---

## 2. Get the code

```powershell
git clone <repo-url> TodoApp
cd TodoApp
git checkout mssql
```

---

## 3. Virtual environment and dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # bash: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> If PowerShell blocks the activate script, run this once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

Check that pyodbc can see the driver:

```powershell
python -c "import pyodbc; print(pyodbc.drivers())"
# must include 'ODBC Driver 18 for SQL Server'
```

---

## 4. Configure `.env`

The app reads settings from environment variables, with `.env` as a local fallback (`app/core/config.py`).
`.env` is **gitignored**. `.env.example` is the committed template, and it holds placeholders only.

```powershell
Copy-Item .env.example .env           # bash: cp .env.example .env
```

Open `.env` and replace the placeholders:

| Key | Value |
|---|---|
| `DATABASE_URL` | Replace `<PASSWORD>` with your login's password, **URL-encoded** (see below) |
| `SECRET_KEY` | A random value: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `MSSQL_SA_PASSWORD` | Only for Docker (step 9): password for the container's `sa` user |

```env
DATABASE_URL=mssql+pyodbc://dev_admin:<PASSWORD>@localhost:1433/todoapplication?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=yes
```

**Anatomy of the URL**

```
mssql+pyodbc://  user : password  @ host : port / database ? driver=...&Encrypt=yes&TrustServerCertificate=yes
└ dialect+driver ┘                                          └ ODBC options ────────────────────────────────┘
```

- `driver=ODBC+Driver+18+for+SQL+Server`: the exact name from `pyodbc.drivers()`, with spaces written as `+`.
- `Encrypt=yes`: Driver 18 encrypts by default (SSMS "Encrypt: Mandatory").
- `TrustServerCertificate=yes`: accepts a local server's self-signed certificate. **Dev only**; see step 10 for production.

**URL-encode special characters in the password:**

| Char | Encoded | | Char | Encoded |
|---|---|---|---|---|
| `@` | `%40` | | `#` | `%23` |
| `:` | `%3A` | | `!` | `%21` |
| `/` | `%2F` | | `%` | `%25` |

```powershell
python -c "from urllib.parse import quote; print(quote('My@Pass#1!', safe=''))"
```

---

## 5. Test the database connection

```powershell
python -c "from sqlalchemy import text; from app.db.database import engine; print(engine.connect().execute(text('SELECT @@VERSION')).scalar())"
```

If this prints `Microsoft SQL Server ...`, the URL, driver, login and network are all good. If it fails, see [Troubleshooting](#11-troubleshooting).

---

## 6. Migrations

**Alembic** versions the schema, much like Git versions code. Each file in `alembic/versions/` is one step, and the database's `alembic_version` table records which step it's at.
`alembic/env.py` reads the same `DATABASE_URL` as the app, so there's nothing to configure in `alembic.ini`.

### 6.1 First run: create the schema

```powershell
python -m scripts.migrate
```

What it does (`scripts/migrate.py`):
- **Empty database** (no `alembic_version` table): creates all tables from the models, then runs `alembic stamp head` to mark the DB as up to date.
- **Existing database**: runs `alembic upgrade head` to apply any pending migrations.

Verify:

```powershell
alembic current     # -> 9f3ba22ed85b (head)
```

In SSMS: `todoapplication` → Tables → `dbo.users`, `dbo.todos`, `dbo.alembic_version`.

### 6.2 Everyday Alembic commands

| Goal | Command |
|---|---|
| Show the DB's current revision | `alembic current` |
| Show all revisions | `alembic history --verbose` |
| Generate a migration from model changes | `alembic revision --autogenerate -m "add due_date to todos"` |
| Create an empty migration (hand-written SQL) | `alembic revision -m "seed roles"` |
| Apply all pending migrations | `alembic upgrade head` |
| Apply the next one only | `alembic upgrade +1` |
| Undo the last migration | `alembic downgrade -1` |
| Undo everything | `alembic downgrade base` |
| Preview SQL without running it | `alembic upgrade head --sql` |
| Mark the DB as current without running anything | `alembic stamp head` |

### 6.3 Worked example: add a column

1. Edit the model in `app/db/models.py`:
   ```python
   from sqlalchemy import DateTime
   class Todos(Base):
       ...
       due_date = Column(DateTime, nullable=True)
   ```
2. Generate the migration:
   ```powershell
   alembic revision --autogenerate -m "add due_date to todos"
   ```
3. **Read the generated file** in `alembic/versions/`. Autogenerate is a draft, not gospel.
4. Apply it, and check it can be rolled back:
   ```powershell
   alembic upgrade head
   alembic downgrade -1
   alembic upgrade head
   ```
5. Commit the model change **and** the migration file together.

**SQL Server-specific gotchas**
- Always give strings a length (`String(100)`). An unbounded `String()` becomes `VARCHAR(max)`, which **can't be indexed or made unique**.
- Adding a `NOT NULL` column to a table that has rows needs a `server_default=...`, or the migration fails.
- SQL Server auto-names default and unique constraints. Dropping such a column can fail with *"The object 'DF__…' is dependent on column"*. Give constraints explicit names, or drop the constraint first in the migration.
- `Boolean` maps to `BIT`, and `Integer, primary_key=True` maps to `INT IDENTITY(1,1)`.

---

## 7. Run the API

```powershell
uvicorn app.main:app --reload
```

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

### 7.1 Try it from the terminal (PowerShell)

```powershell
$base = "http://127.0.0.1:8000"

# 1. Register
$user = @{ username='alice'; email='alice@example.com'; first_name='Alice'; last_name='Doe'; password='secret123' } | ConvertTo-Json
Invoke-RestMethod -Method Post "$base/auth/user" -ContentType 'application/json' -Body $user

# 2. Log in (OAuth2 form) and keep the token
$tok = Invoke-RestMethod -Method Post "$base/auth/token" -ContentType 'application/x-www-form-urlencoded' -Body 'username=alice&password=secret123'
$h = @{ Authorization = "Bearer $($tok.access_token)" }

# 3. Create and list todos
$todo = @{ title='Learn MSSQL'; description='Run the guide end to end'; priority=2 } | ConvertTo-Json
Invoke-RestMethod -Method Post "$base/todos" -Headers $h -ContentType 'application/json' -Body $todo
Invoke-RestMethod "$base/todos" -Headers $h
```

bash / curl equivalent:

```bash
curl -X POST localhost:8000/auth/user -H 'Content-Type: application/json' \
  -d '{"username":"alice","email":"alice@example.com","first_name":"Alice","last_name":"Doe","password":"secret123"}'
TOKEN=$(curl -s -X POST localhost:8000/auth/token -d 'username=alice&password=secret123' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
curl -X POST localhost:8000/todos -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"title":"Learn MSSQL","description":"Run the guide end to end","priority":2}'
curl localhost:8000/todos -H "Authorization: Bearer $TOKEN"
```

### 7.2 See the rows in SQL Server

```sql
USE todoapplication;
SELECT id, username, email, role FROM dbo.users;
SELECT * FROM dbo.todos;
```

---

## 8. Run the tests

```powershell
pytest            # or: pytest -v, pytest tests/test_todos.py -k create
```

Tests use a throwaway **SQLite** file (`tests/conftest.py` forces `DATABASE_URL=sqlite:///./test.db`). That means:
- tests can never touch your real SQL Server data;
- they run fast and need no database server in CI;
- they still exercise the same SQLAlchemy models, so they catch most bugs. Database-specific behaviour (constraint names, collations) is what the smoke test in step 7 is for.

---

## 9. Run everything in Docker (local)

`docker-compose.yml` starts three services:

| Service | What it does |
|---|---|
| `db` | SQL Server 2022 (Linux) on host port **1434**, so it doesn't clash with a local SQL Server on 1433 |
| `db-init` | One-shot: waits for `db` to be healthy, runs `CREATE DATABASE todoapplication` if missing, then exits |
| `api` | Builds the `Dockerfile` (installs ODBC Driver 18), runs `python -m scripts.migrate`, then uvicorn on port **8000** |

### 9.1 Set the container password
In `.env`, set `MSSQL_SA_PASSWORD`. It needs **8+ characters with 3 of: uppercase, lowercase, digit, symbol**, or the SQL Server container exits immediately. Avoid `@ : / #` here, because it's also embedded in the API's connection URL.
Compose refuses to start if it's missing (`required variable MSSQL_SA_PASSWORD is missing`).

### 9.2 Start, watch, stop

```powershell
docker compose up --build -d          # build the image and start everything in the background
docker compose ps                     # db: healthy, db-init: exited (0), api: running
docker compose logs -f api            # follow API logs (Ctrl+C to stop following)
```

Open http://localhost:8000/docs.

Connect SSMS to the container database: **Server** `localhost,1434` · **Login** `sa` · **Password** = `MSSQL_SA_PASSWORD` · tick *Trust server certificate*.

```powershell
docker compose exec api alembic current          # migration state inside the container
docker compose exec api python -m scripts.migrate  # re-run migrations after adding new ones
docker compose restart api                       # restart only the API
docker compose down                              # stop and remove containers (data kept in volume)
docker compose down -v                           # ...and delete the database volume (fresh start)
```

> Inside the compose network the API reaches the database at host **`db`**, not `localhost`. That's why `docker-compose.yml` overrides `DATABASE_URL` for the `api` service.

---

## 10. Deploy with Docker

The same image runs on any server or cloud. Only environment variables change ([12-factor](https://12factor.net/config)).

### 10.1 Build, tag and push the image

```powershell
docker build -t todo-api:1.0.0 .

# Docker Hub
docker login
docker tag todo-api:1.0.0 <dockerhub-user>/todo-api:1.0.0
docker push <dockerhub-user>/todo-api:1.0.0

# or Azure Container Registry
az acr login --name <registry>
docker tag todo-api:1.0.0 <registry>.azurecr.io/todo-api:1.0.0
docker push <registry>.azurecr.io/todo-api:1.0.0
```

### 10.2 Production environment file
Create `prod.env` **on the server** (never in Git):

```env
APP_ENV=production
SECRET_KEY=<64-hex-chars from secrets.token_hex(32)>
ACCESS_TOKEN_EXPIRE_MINUTES=20
# Azure SQL / a server with a real TLS certificate: keep Encrypt, DROP TrustServerCertificate
DATABASE_URL=mssql+pyodbc://<user>:<url-encoded-password>@<server>.database.windows.net:1433/todoapplication?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes
```

In production, use a **managed database** (Azure SQL, AWS RDS for SQL Server) or a dedicated server rather than the compose `db` container. You get backups, high availability and patching.

### 10.3 Run migrations as a release step, then start the app

```powershell
# 1. Migrate once per release (one-off container)
docker run --rm --env-file prod.env <registry>/todo-api:1.0.0 python -m scripts.migrate

# 2. Start the API with gunicorn managing multiple uvicorn workers
docker run -d --name todo-api --restart unless-stopped -p 8000:8000 --env-file prod.env `
  <registry>/todo-api:1.0.0 `
  gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000
```

(bash: replace the PowerShell line continuation `` ` `` with `\`.)

> gunicorn is Linux/macOS only (it needs `fcntl`). It works inside the container on any host, but running it directly on Windows fails. On Windows, use `uvicorn app.main:app --workers 4` instead.

Why split them? If several replicas started at once and each ran migrations, they could race each other. Migrating once, before the rollout, is safe.

### 10.4 Production checklist
- [ ] HTTPS in front of the app (Nginx/Caddy/Traefik, or the cloud's load balancer); the container listens on plain HTTP.
- [ ] Real `SECRET_KEY`, unique per environment; rotating it logs everyone out.
- [ ] DB login with **least privilege** for the app (`db_datareader` + `db_datawriter`), and a separate login for migrations.
- [ ] `TrustServerCertificate` removed; the server has a valid certificate.
- [ ] Firewall: only the app can reach port 1433.
- [ ] Image tagged with a version (`1.0.0`), never only `latest`; rollback = run the previous tag.
- [ ] Logs collected from stdout (`docker logs`, or the platform's log service).

### 10.5 Updating a deployment

```powershell
git pull; docker build -t <registry>/todo-api:1.0.1 .; docker push <registry>/todo-api:1.0.1
# on the server:
docker pull <registry>/todo-api:1.0.1
docker run --rm --env-file prod.env <registry>/todo-api:1.0.1 python -m scripts.migrate
docker stop todo-api; docker rm todo-api
docker run -d --name todo-api --restart unless-stopped -p 8000:8000 --env-file prod.env <registry>/todo-api:1.0.1 `
  gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000
```

---

## 11. Troubleshooting

| Error (excerpt) | Cause | Fix |
|---|---|---|
| `IM002 Data source name not found and no default driver specified` | Driver name in the URL doesn't match an installed driver | Run `python -c "import pyodbc; print(pyodbc.drivers())"` and copy the exact name (spaces → `+`) |
| `18456 Login failed for user` | Wrong password, or SQL auth disabled | Check the password (and its URL-encoding); enable mixed-mode auth (step 1.1) and restart |
| `SSL Provider: The certificate chain was issued by an authority that is not trusted` | Driver 18 encrypts by default; the local cert is self-signed | Add `TrustServerCertificate=yes` (dev only) |
| `TCP Provider: No connection could be made` / `08001` timeout | TCP/IP disabled, service stopped, wrong port | Step 1.2; `Get-Service MSSQLSERVER`; check the port |
| `Cannot open database "todoapplication" requested by the login` | Database not created, or the login has no user in it | Step 1.3 |
| `CREATE TABLE permission denied` | Login isn't `db_owner` / lacks DDL rights | `ALTER ROLE db_owner ADD MEMBER dev_admin;` |
| `ImportError: cannot import name 'command' from 'alembic'` | Alembic isn't installed in the active venv, so the project's `alembic/` folder shadows it | Activate the venv and run `pip install -r requirements.txt` |
| Container `db` keeps restarting / exits | `MSSQL_SA_PASSWORD` too weak | Use 8+ chars with upper/lower/digit/symbol, then `docker compose down -v` and `up` again |
| `required variable MSSQL_SA_PASSWORD is missing` | Not set in `.env` | Add it (step 9.1) |
| `port is already allocated` on 1434/8000 | Something else is using the port | Change the left side of the `ports:` mapping in `docker-compose.yml` |
| Column can't be dropped: `object 'DF__…' is dependent on column` | Auto-named default constraint | Drop the constraint in the migration first (step 6.3 gotchas) |

---

## 12. Command cheat sheet

```powershell
# one-time setup
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
Copy-Item .env.example .env        # then fill in placeholders

# database
python -m scripts.migrate                          # create or upgrade the schema
alembic revision --autogenerate -m "message"       # new migration from model changes
alembic upgrade head | alembic downgrade -1 | alembic current | alembic history

# run and test
uvicorn app.main:app --reload                      # http://127.0.0.1:8000/docs
pytest -v

# docker
docker compose up --build -d; docker compose logs -f api; docker compose down [-v]
docker build -t todo-api:1.0.0 .
```
