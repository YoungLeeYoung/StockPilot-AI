# Development guide

## Environments

- `development`: local machines and local Docker services
- `test`: automated tests with isolated dependencies
- `production`: managed infrastructure and external secrets

Real credentials must be stored in ignored `.env` files or a deployment secret manager. Example files contain names and safe local defaults only.

## Service ports

| Service | Port |
| --- | ---: |
| Frontend | 5173 |
| Backend | 8000 |
| PostgreSQL | 5432 |
| Redis | 6379 |

## Development workflow

1. Start PostgreSQL and Redis with Docker Compose.
2. Run FastAPI in a Python virtual environment.
3. Run Vite in a separate terminal.
4. Run linting and tests before submitting changes.

## Configuration ownership

- Root `.env`: local container configuration
- `backend/.env`: backend runtime configuration and provider secrets
- `frontend/.env.local`: browser-safe frontend configuration

Only variables prefixed with `VITE_` are exposed to frontend code. Secret API keys must remain in the backend environment.

