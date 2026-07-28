# Docker Deployment

StockPilot AI is deployed as three Docker Compose services:

- `frontend`: builds the React application and serves it with Nginx
- `backend`: runs Alembic migrations, then starts FastAPI with Uvicorn
- `postgres`: stores application data in a named Docker volume

The browser sends API requests through Nginx at `/api/v1`, so no public API URL needs to be embedded in the frontend build.

## Requirements

- Docker Desktop with Docker Compose v2
- Ports `80` and `8000` available, or alternative ports configured in `.env`

## First deployment

Run these commands from the project root:

```powershell
Copy-Item .env.example .env
notepad .env
docker compose up -d --build
docker compose ps
```

Change `POSTGRES_PASSWORD` before the first start. Use URL-safe characters in the password because it is included in `DATABASE_URL`; percent-encode reserved URL characters such as `@`, `:`, `/`, and `%` when necessary.

The default endpoints are:

- Web application: `http://localhost`
- API documentation through Nginx: `http://localhost/docs`
- Backend health check: `http://localhost:8000/api/v1/health`

The backend waits for PostgreSQL to become healthy and applies all Alembic migrations before Uvicorn starts. AI endpoints require a configured LLM provider and API key; the rest of the application can run without them.

## Configuration

The root `.env` controls host ports, database credentials, CORS, LLM settings, and PDF upload limits. Restart the affected containers after editing it:

```powershell
docker compose up -d --build
```

PostgreSQL and the backend bind to `127.0.0.1` by default. For a public deployment, place a TLS reverse proxy or load balancer in front of the frontend and do not expose PostgreSQL publicly.

## Operations

```powershell
# Show container status
docker compose ps

# Follow logs
docker compose logs -f backend frontend postgres

# Apply or inspect database migrations
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current

# Rebuild after an application update
docker compose up -d --build

# Stop containers while preserving data
docker compose down
```

`docker compose down -v` also deletes the PostgreSQL data volume. Use it only when permanent data removal is intended.

## Backup and restore

Create a SQL backup from PowerShell:

```powershell
docker compose exec -T postgres pg_dump -U stockpilot -d stockpilot --clean --if-exists | Set-Content -Encoding utf8 stockpilot-backup.sql
```

Restore a backup into a running database:

```powershell
Get-Content stockpilot-backup.sql | docker compose exec -T postgres psql -U stockpilot -d stockpilot
```

Adjust the database user and name if `POSTGRES_USER` or `POSTGRES_DB` was changed.

## Troubleshooting

Use `docker compose ps` first: `postgres`, `backend`, and `frontend` should all become healthy. If the backend does not start, inspect `docker compose logs backend postgres`; migration and database connection errors appear there. If a host port is already occupied, change `FRONTEND_PORT`, `BACKEND_PORT`, or `POSTGRES_PORT` in `.env` and restart the stack.
