from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.core.database import get_db
from src.core.limiter import limiter
from src.user.models import User
from src.video.exceptions import (
    InvalidProjectStatus,
    ProjectNotFound,
    ProjectNotOwnedByUser,
    VideoGenerationFailed,
)
from src.video.schemas import (
    GenerationStatusRead,
    MetadataApprove,
    ProjectCreate,
    ProjectListItem,
    ProjectRead,
    PromptApprove,
    PromptRegenerate,
    PromptSave,
    VideoApprove,
    YouTubePublishResponse,
)
from src.video.service import VideoService

router = APIRouter(prefix="/video", tags=["video"])


def _service(db: AsyncSession = Depends(get_db)) -> VideoService:
    return VideoService(db)


def _handle_common(exc: Exception) -> None:
    if isinstance(exc, ProjectNotFound):
        raise HTTPException(status_code=404, detail="Project not found")
    if isinstance(exc, ProjectNotOwnedByUser):
        raise HTTPException(status_code=403, detail="Access denied")
    if isinstance(exc, InvalidProjectStatus):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot perform action: current={exc.current!r}, required={exc.required!r}",
        )
    if isinstance(exc, VideoGenerationFailed):
        raise HTTPException(status_code=500, detail=f"Generation failed: {exc}")
    raise exc


@router.post("/projects", response_model=ProjectRead)
@limiter.limit("10/minute")
async def create_project(
    request: Request,
    body: ProjectCreate,
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(_service),
) -> ProjectRead:
    try:
        project = await service.create_project(current_user.id, body.topic)
    except Exception as exc:
        _handle_common(exc)
    return ProjectRead.model_validate(project)


@router.get("/projects", response_model=list[ProjectListItem])
async def list_projects(
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(_service),
) -> list[ProjectListItem]:
    projects = await service.list_projects(current_user.id)
    return [ProjectListItem.model_validate(p) for p in projects]


@router.get("/projects/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(_service),
) -> ProjectRead:
    try:
        project = await service.get_project(project_id, current_user.id)
    except Exception as exc:
        _handle_common(exc)
    return ProjectRead.model_validate(project)


@router.post("/projects/{project_id}/save-prompt", response_model=ProjectRead)
async def save_prompt(
    project_id: int,
    body: PromptSave,
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(_service),
) -> ProjectRead:
    try:
        project = await service.save_prompt(project_id, current_user.id, body.edited_prompt)
    except Exception as exc:
        _handle_common(exc)
    return ProjectRead.model_validate(project)


@router.post("/projects/{project_id}/approve-prompt", response_model=ProjectRead)
@limiter.limit("10/minute")
async def approve_prompt(
    request: Request,
    project_id: int,
    body: PromptApprove,
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(_service),
) -> ProjectRead:
    try:
        project = await service.approve_prompt(project_id, current_user.id, body.edited_prompt)
    except Exception as exc:
        _handle_common(exc)
    return ProjectRead.model_validate(project)


@router.post("/projects/{project_id}/regenerate-prompt", response_model=ProjectRead)
@limiter.limit("10/minute")
async def regenerate_prompt(
    request: Request,
    project_id: int,
    body: PromptRegenerate = PromptRegenerate(),
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(_service),
) -> ProjectRead:
    try:
        project = await service.regenerate_prompt(
            project_id, current_user.id, instruction=body.instruction
        )
    except Exception as exc:
        _handle_common(exc)
    return ProjectRead.model_validate(project)


@router.get("/projects/{project_id}/generation-status", response_model=GenerationStatusRead)
async def get_generation_status(
    project_id: int,
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(_service),
) -> GenerationStatusRead:
    try:
        return await service.get_generation_status(project_id, current_user.id)
    except Exception as exc:
        _handle_common(exc)


@router.post("/projects/{project_id}/approve-video", response_model=ProjectRead)
@limiter.limit("10/minute")
async def approve_video(
    request: Request,
    project_id: int,
    body: VideoApprove,
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(_service),
) -> ProjectRead:
    try:
        project = await service.approve_video(project_id, current_user.id, body.approved)
    except Exception as exc:
        _handle_common(exc)
    return ProjectRead.model_validate(project)


@router.post("/projects/{project_id}/approve-metadata", response_model=ProjectRead)
async def approve_metadata(
    project_id: int,
    body: MetadataApprove,
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(_service),
) -> ProjectRead:
    try:
        project = await service.approve_metadata(
            project_id, current_user.id, body.edited_title, body.edited_description
        )
    except Exception as exc:
        _handle_common(exc)
    return ProjectRead.model_validate(project)


@router.post("/projects/{project_id}/add-part", response_model=ProjectRead)
async def add_part(
    project_id: int,
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(_service),
) -> ProjectRead:
    """Add a new video part (max 3). Triggers prompt generation for the next part."""
    try:
        project = await service.add_part(project_id, current_user.id)
    except Exception as exc:
        _handle_common(exc)
    return ProjectRead.model_validate(project)


@router.post("/projects/{project_id}/finalize-parts", response_model=ProjectRead)
async def finalize_parts(
    project_id: int,
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(_service),
) -> ProjectRead:
    """Finalize all parts and move to metadata generation."""
    try:
        project = await service.finalize_parts(project_id, current_user.id)
    except Exception as exc:
        _handle_common(exc)
    return ProjectRead.model_validate(project)


@router.get("/projects/{project_id}/download")
async def get_download(
    project_id: int,
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(_service),
) -> dict:
    try:
        video_url = await service.get_download_info(project_id, current_user.id)
    except Exception as exc:
        _handle_common(exc)
    return {"video_url": video_url}


@router.post("/projects/{project_id}/publish-youtube")
async def publish_youtube(
    project_id: int,
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(_service),
    db: AsyncSession = Depends(get_db),
):
    """Delegate to the YouTube router's publish endpoint."""
    from src.youtube.router import publish_project
    from src.youtube.schemas import YouTubePublishRequest
    from src.youtube.service import YouTubeService

    return await publish_project(
        project_id=project_id,
        body=YouTubePublishRequest(),
        current_user=current_user,
        svc=YouTubeService(db),
        db=db,
    )
