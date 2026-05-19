# Auth Session API

Session-based authentication backend with email confirmation. Built with FastAPI, PostgreSQL, Redis, and Celery.

## Features

- User registration and login
- Secure session management (30-day sessions, stored hashed)
- Email confirmation via token (required before login)
- Background email delivery (Resend API or Gmail SMTP fallback)
- Rate limiting on auth endpoints
- Async throughout (SQLAlchemy async, asyncpg)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI + Uvicorn |
| Database | PostgreSQL 17 + SQLAlchemy 2 + Alembic |
| Cache / Broker | Redis 7 |
| Background jobs | Celery 5 |
| Email | Resend API / Gmail SMTP |
| Runtime | Python 3.14 + uv |

## Quick Start

**Prerequisites:** Docker and Docker Compose.

```bash
git clone <repo-url>
cd youtube-video-generator

cp .env.example .env
# Edit .env and fill in required values (see Configuration below)

docker compose run --rm migrate   # apply DB migrations
docker compose up                 # start API + worker + Redis + Postgres
```

API is available at http://localhost:8000  
Interactive docs at http://localhost:8000/docs

## API Reference

### Auth

| Method | Endpoint | Description | Rate limit |
|--------|----------|-------------|-----------|
| `POST` | `/auth/register` | Create account, sends confirmation email | 5/min |
| `POST` | `/auth/login` | Login (requires confirmed email) | 10/min |
| `POST` | `/auth/logout` | Invalidate current session | — |
| `GET` | `/auth/confirm-email?token=<token>` | Confirm email address | 10/min |

### User

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/users/get-me` | Current user info + active sessions |

### Register

```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "Secret123!"
}
```

Password requirements: 8+ characters, 1 uppercase, 1 digit, 1 symbol.

### Login

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "Secret123!"
}
```

Returns a session token in a cookie. The account must have a confirmed email.

## Configuration

Copy `.env.example` to `.env` and set the following:

```env
# PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/dbname
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=dbname
POSTGRES_USER=user
POSTGRES_PASSWORD=pass

# Celery (Redis)
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# Redis (app use)
REDIS_URL=redis://redis:6379/0

# Email — Resend (primary)
RESEND_API_KEY=re_your_api_key_here

# Email — Gmail SMTP (fallback)
SENDER_EMAIL=you@gmail.com
EMAIL_APP_PASSWORD=your_app_password

# App
BASE_URL=http://localhost:8000
ORIGINS=["http://localhost:3000"]
HTTPS_REDIRECT=false
```

## Project Structure

```
backend/
├── src/
│   ├── main.py              # App entry point, middleware
│   ├── core/                # Config, DB, security, rate limiter
│   ├── auth/                # Auth routes and business logic
│   ├── user/                # User model, schemas, service, repository
│   ├── session/             # Session model, schemas, service, repository
│   └── celery_app/          # Celery config + email tasks
├── alembic/                 # Database migrations
└── pyproject.toml
docker-compose.yml
```

## Development

```bash
cd backend
uv sync                          # install dependencies

uv run uvicorn src.main:app --reload          # local API
uv run celery -A src.celery_app.celery_main:celery_app worker --loglevel=info

uv run alembic upgrade head                   # apply migrations
uv run alembic revision --autogenerate -m ""  # generate migration

uv run pytest                                 # tests
uv run ruff check . && uv run ruff format .   # lint + format
```

## License

[MIT](LICENSE)
