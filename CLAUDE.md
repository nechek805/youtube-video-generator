# CLAUDE.md

## Project Overview

Session-based authentication API built with FastAPI, PostgreSQL, Redis, and Celery. Handles user registration, login/logout, email confirmation, and session management.

## Tech Stack

- **Runtime:** Python 3.14, `uv` package manager
- **API:** FastAPI + Uvicorn
- **Database:** PostgreSQL 17 + SQLAlchemy 2 (async) + Alembic
- **Cache / Broker:** Redis 7 (db 0 = app cache, db 1 = Celery broker, db 2 = Celery results)
- **Background jobs:** Celery 5
- **Email:** Resend API (primary), Gmail SMTP (fallback)

## Repository Layout

```
backend/
  src/
    main.py              # FastAPI app, middleware, routers
    core/                # config, DB session, security helpers, rate limiter
    auth/                # register / login / logout / confirm-email routes
    user/                # user model, schemas, service, repository
    session/             # session model, schemas, service, repository
    celery_app/          # Celery setup + email tasks
  alembic/               # migrations
  pyproject.toml
docker-compose.yml
.env.example
```

## Running the Stack

```bash
# Copy and fill in env vars
cp .env.example .env

# Run everything
docker compose up

# Run migrations (one-off)
docker compose run --rm migrate
```

Services:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

## Common Dev Commands

All commands run from `backend/` using `uv`:

```bash
# Install dependencies
uv sync

# Run API locally (outside Docker)
uv run uvicorn src.main:app --reload

# Run Celery worker locally
uv run celery -A src.celery_app.celery_main:celery_app worker --loglevel=info

# Apply migrations
uv run alembic upgrade head

# Create a migration
uv run alembic revision --autogenerate -m "description"

# Lint / format
uv run ruff check .
uv run ruff format .

# Tests
uv run pytest
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check |
| POST | `/auth/register` | Register (5 req/min) |
| POST | `/auth/login` | Login (10 req/min) |
| POST | `/auth/logout` | Logout |
| GET | `/auth/confirm-email` | Confirm email via token |
| GET | `/users/get-me` | Current user + sessions |

## Architecture Patterns

- **Router → Service → Repository** layering — business logic lives in services, not routers.
- **Tokens are hashed at rest** — session and email-confirmation tokens are stored as SHA-256 hashes; the raw token is returned to the client only once.
- **Email confirmation is required before login** — users with `PENDING` status are rejected at login.
- **Celery tasks are fire-and-forget** — email delivery failures do not affect the API response.

## Environment Variables

See `.env.example` for the full list. Key variables:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | asyncpg PostgreSQL DSN |
| `CELERY_BROKER_URL` | Redis DSN (db 1) |
| `CELERY_RESULT_BACKEND` | Redis DSN (db 2) |
| `REDIS_URL` | Redis DSN (db 0) for app use |
| `RESEND_API_KEY` | Resend email API key |
| `BASE_URL` | Public API URL (used in confirmation links) |
| `ORIGINS` | JSON array of allowed CORS origins |
| `HTTPS_REDIRECT` | `true` to force HTTPS |

## Database Migrations

Alembic is configured in `backend/alembic.ini`. The `migrate` Docker Compose service runs `alembic upgrade head` on startup and exits.

Always generate migrations with `--autogenerate` and review the output before committing.
