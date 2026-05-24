# AGENTS.md

## Project Overview

YouTube Video Generator MVP. Users log in, enter a video topic, get an AI-generated prompt, generate a mock video, then get AI-written YouTube title and description. Built on a session-based FastAPI auth backend with a React frontend.

## Tech Stack

- **Runtime:** Python 3.14, `uv` package manager
- **API:** FastAPI + Uvicorn
- **Database:** PostgreSQL 17 + SQLAlchemy 2 (async) + Alembic
- **Cache / Broker:** Redis 7 (db 0 = app cache, db 1 = Celery broker, db 2 = Celery results)
- **Background jobs:** Celery 5
- **LLM workflow:** LangGraph + langchain-openai (gpt-4o-mini)
- **Email:** Resend API (primary), Gmail SMTP (fallback)
- **Frontend:** React 18 + Vite + TypeScript + Tailwind CSS + React Query + React Router v6

## Repository Layout

```
backend/
  src/
    main.py              # FastAPI app, middleware, routers
    core/                # config, DB session, security helpers, rate limiter
    auth/                # register / login / logout / confirm-email routes
    user/                # user model, schemas, service, repository
    session/             # session model, schemas, service, repository
    video/               # video workflow: models, schemas, service, repository, router, langgraph
    celery_app/          # Celery setup + email tasks + video generation task
  alembic/               # migrations
  pyproject.toml
frontend/
  src/
    api/                 # apiFetch client, auth.ts, projects.ts
    components/          # Layout, ProtectedRoute, StepIndicator, PromptEditor, VideoPlayer, MetadataEditor
    hooks/               # React Query hooks for all mutations and queries
    pages/               # LoginPage, RegisterPage, DashboardPage, NewProjectPage, ProjectPage
    types/               # TypeScript interfaces mirroring backend schemas
docker-compose.yml
.env.example
```

## Running the Stack

```bash
# Copy and fill in env vars (OPENAI_API_KEY required)
cp .env.example .env

# Run migrations
docker compose run --rm migrate

# Run everything
docker compose up
```

Services:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

## Common Dev Commands

Backend (`backend/`):
```bash
uv sync
uv run uvicorn src.main:app --reload
uv run celery -A src.celery_app.celery_main:celery_app worker --loglevel=info
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"
uv run ruff check . && uv run ruff format .
uv run pytest
```

Frontend (`frontend/`):
```bash
npm install
npm run dev        # http://localhost:5173 (with proxy to :8000)
npx tsc --noEmit   # type-check
```

## API Endpoints

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Register (5 req/min) |
| POST | `/auth/login` | Login (10 req/min) |
| POST | `/auth/logout` | Logout |
| GET | `/auth/confirm-email` | Confirm email via token |
| GET | `/users/get-me` | Current user + sessions |

### Video Workflow
| Method | Path | Description | Rate limit |
|--------|------|-------------|-----------|
| POST | `/video/projects` | Create project, run LLM → workflow=PROMPT, prompt=READY | 10/min |
| GET | `/video/projects` | List user's projects | — |
| GET | `/video/projects/{id}` | Get project + generation_steps | — |
| POST | `/video/projects/{id}/approve-prompt` | Approve/edit prompt → start video gen | 10/min |
| POST | `/video/projects/{id}/regenerate-prompt` | Re-run prompt LLM | 10/min |
| GET | `/video/projects/{id}/generation-status` | Poll while video_status=GENERATING | — |
| POST | `/video/projects/{id}/approve-video` | Approve/reject video → run LLM metadata | 10/min |
| POST | `/video/projects/{id}/approve-metadata` | Approve/edit metadata → COMPLETED | — |
| GET | `/video/projects/{id}/download` | Get video URL | — |
| POST | `/video/projects/{id}/publish-youtube` | YouTube publish stub | — |

## Video Workflow State Machine

`VideoProject` has four independent status columns:

```
workflow_status :  PROMPT  →  VIDEO  →  METADATA  →  COMPLETED
                     ↑           │
                     └─reject────┘                  (FAILED on any error)

prompt_status   :  PENDING → READY  (or FAILED)
video_status    :  PENDING → GENERATING → READY  (or FAILED)
metadata_status :  PENDING → READY  (or FAILED)
```

`workflow_status` is the user-facing phase; each phase status tracks
work inside that phase. The LangGraph workflow has seven nodes:
`generate_prompt`, `wait_for_prompt_approval`, `generate_video`,
`wait_for_video_approval`, `generate_metadata`,
`wait_for_metadata_approval`, `finalize_project`, plus an auxiliary
`reject_video` node. See `backend/src/video/workflow.py`.

## Architecture Patterns

- **Router → Service → Repository** — business logic in services, raw DB in repositories.
- **New module pattern:** create `models.py`, `schemas.py`, `exceptions.py`, `repository.py`, `service.py`, `router.py` under `src/<module>/`. Register router in `main.py`. Add model import in `alembic/env.py`.
- **Protected routes:** `Depends(get_current_user)` + `Depends(get_db)`.
- **LangGraph calls run inline** in FastAPI async event loop via `graph.ainvoke()` — fast enough at 2–5 s.
- **Celery video task** uses a sync SQLAlchemy session (not the async engine). DSN is converted from `asyncpg://` to `psycopg://` inside the task.
- **Tokens are hashed at rest** — SHA-256, raw token sent once.

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | asyncpg PostgreSQL DSN |
| `CELERY_BROKER_URL` | Redis DSN (db 1) |
| `CELERY_RESULT_BACKEND` | Redis DSN (db 2) |
| `REDIS_URL` | Redis DSN (db 0) |
| `LLM_PROVIDER` | LLM provider: `openai` (default) or `mock` (auto when no API key) |
| `OPENAI_API_KEY` | OpenAI key for LangGraph LLM calls (empty → mock fallback) |
| `OPENAI_MODEL` | Model name (default: gpt-4o-mini) |
| `MOCK_VIDEO_CDN_BASE` | Base URL for mock video files |
| `VIDEO_PROVIDER` | Active video provider: `mock` (default), `runway`, `pika`, `luma`, `kling` |
| `MOCK_VIDEO_MODE` | Mock-only: `placeholder` (default) or `static` (serves `/static/sample.mp4`) |
| `RUNWAY_API_KEY` / `PIKA_API_KEY` / `LUMA_API_KEY` / `KLING_API_KEY` | Reserved for future provider integrations |
| `RESEND_API_KEY` | Resend email API key |
| `BASE_URL` | Public API URL (used in confirmation links) |
| `ORIGINS` | JSON array of allowed CORS origins |

## Video Providers

Provider classes live in `backend/src/video/services/video_providers/` — one file per provider, each subclassing `VideoProvider` (in `base.py`). The active provider is selected by the `VIDEO_PROVIDER` env var and built by `factory.get_video_provider()`. Adding a real provider is a single-file change: implement `async generate(...)` and wire it into the factory.

Only `mock` is wired up today; Runway/Pika/Luma/Kling subclasses exist as stubs that raise `NotImplementedError`.

## Database Migrations

Two migrations: `0001_initial` (auth tables) and `0002_add_video_tables` (video_projects, video_generations, projectstatus enum).

Always generate with `--autogenerate` and review before committing. Model must be imported in `alembic/env.py`.
