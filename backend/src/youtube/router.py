"""YouTube OAuth connect/disconnect endpoints and video publishing.

OAuth flow:
  GET  /youtube/connect           → redirect user to Google consent screen
  GET  /youtube/callback          → Google redirects here with ?code=...
  DELETE /youtube/disconnect      → revoke stored tokens for current user
  GET  /youtube/account           → return connected channel info (or 404)
"""
import secrets

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.core.config import config
from src.core.database import get_db
from src.user.models import User
from src.youtube.exceptions import (
    YouTubeAccountNotFound,
    YouTubeOAuthError,
    YouTubeUploadError,
)
from src.youtube.oauth import build_auth_url
from src.youtube.schemas import YouTubeAccountRead, YouTubePublishRequest, YouTubePublishResult
from src.youtube.service import YouTubeService

router = APIRouter(prefix="/youtube", tags=["youtube"])


def _svc(db: AsyncSession = Depends(get_db)) -> YouTubeService:
    return YouTubeService(db)


# ---------------------------------------------------------------------------
# OAuth connect
# ---------------------------------------------------------------------------

@router.get("/connect")
async def connect_youtube(
    current_user: User = Depends(get_current_user),
):
    """Redirect the browser to Google's OAuth consent screen."""
    # state = random token to prevent CSRF (simple approach — no session needed
    # for MVP; full production would store it in Redis and verify on callback)
    state = secrets.token_urlsafe(16)
    url = build_auth_url(state=state)
    return RedirectResponse(url)


@router.get("/callback")
async def youtube_callback(
    code: str | None = None,
    error: str | None = None,
    current_user: User = Depends(get_current_user),
    svc: YouTubeService = Depends(_svc),
):
    """Google redirects here after the user approves (or denies) access."""
    if error or not code:
        raise HTTPException(
            status_code=400,
            detail=f"Google OAuth error: {error or 'no code returned'}",
        )

    try:
        account = await svc.connect(current_user.id, code)
    except YouTubeOAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Redirect back to the frontend settings page after connecting.
    frontend_origin = config.get_origins()[0] if config.get_origins() else "http://localhost:3000"
    return RedirectResponse(
        f"{frontend_origin}/settings?youtube=connected"
    )


# ---------------------------------------------------------------------------
# Account info & disconnect
# ---------------------------------------------------------------------------

@router.get("/account", response_model=YouTubeAccountRead)
async def get_youtube_account(
    current_user: User = Depends(get_current_user),
    svc: YouTubeService = Depends(_svc),
) -> YouTubeAccountRead:
    """Return the connected YouTube channel info for the current user."""
    try:
        account = await svc.get_account(current_user.id)
    except YouTubeAccountNotFound:
        raise HTTPException(status_code=404, detail="No YouTube account connected")
    return YouTubeAccountRead.model_validate(account)


@router.delete("/disconnect", status_code=204)
async def disconnect_youtube(
    current_user: User = Depends(get_current_user),
    svc: YouTubeService = Depends(_svc),
) -> None:
    """Remove stored YouTube tokens for the current user."""
    try:
        await svc.disconnect(current_user.id)
    except YouTubeAccountNotFound:
        raise HTTPException(status_code=404, detail="No YouTube account connected")


# ---------------------------------------------------------------------------
# Publish a project's video to YouTube
# (also wired into /video/projects/{id}/publish-youtube below)
# ---------------------------------------------------------------------------

@router.post(
    "/projects/{project_id}/publish",
    response_model=YouTubePublishResult,
)
async def publish_project(
    project_id: int,
    body: YouTubePublishRequest | None = None,
    current_user: User = Depends(get_current_user),
    svc: YouTubeService = Depends(_svc),
    db: AsyncSession = Depends(get_db),
) -> YouTubePublishResult:
    """Upload the completed project video to the user's YouTube channel."""
    from src.video.service import VideoService

    body = body or YouTubePublishRequest()
    video_svc = VideoService(db)

    try:
        project = await video_svc.get_project(project_id, current_user.id)
    except Exception:
        raise HTTPException(status_code=404, detail="Project not found")

    # Collect video URLs: use the ordered list of approved parts when the
    # project has multiple parts; fall back to the single project.video_url.
    if project.parts:
        video_urls = [p.video_url for p in sorted(project.parts, key=lambda p: p.part_number)]
    elif project.video_url:
        video_urls = [project.video_url]
    else:
        raise HTTPException(status_code=409, detail="Project has no video yet")

    title = body.title or project.title or project.topic
    description = body.description or project.description or ""
    tags = body.tags or project.tags or []

    try:
        result = await svc.upload_video(
            user_id=current_user.id,
            video_urls=video_urls,
            title=title,
            description=description,
            tags=tags,
            privacy=body.privacy,
        )
    except YouTubeAccountNotFound:
        raise HTTPException(
            status_code=400,
            detail="No YouTube account connected. Visit /youtube/connect first.",
        )
    except YouTubeUploadError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    return result
