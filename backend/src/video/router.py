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
    PromptEdit,
    YouTubePublishResponse,
)
from src.video.service import VideoService

router = APIRouter(prefix="/video-projects", tags=["video-projects"])


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


# ----------------------------------------------------------------------
# Projects: CRUD-style
# ----------------------------------------------------------------------

@router.post("", response_model=ProjectRead)
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


@router.get("", response_model=list[ProjectListItem])
async def list_projects(
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(_service),
) -> list[ProjectListItem]:
    projects = await service.list_projects(current_user.id)
    return [ProjectListItem.model_validate(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectRead)
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


# ----------------------------------------------------------------------
# Prompt phase
# ----------------------------------------------------------------------

@router.post("/{project_id}/generate-prompt", response_model=ProjectRead)
@limiter.limit("10/minute")
async def generate_prompt(
    request: Request,
    project_id: int,
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(_service),
) -> ProjectRead:
    try:
        project = await service.generate_prompt(project_id, current_user.id)
    except Exception as exc:
        _handle_common(exc)
    return ProjectRead.model_validate(project)


@router.post("/{project_id}/edit-prompt", response_model=ProjectRead)
async def edit_prompt(
    project_id: int,
    body: PromptEdit,
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(_service),
) -> ProjectRead:
    try:
        project = await service.edit_prompt(project_id, current_user.id, body.edited_prompt)
    except Exception as exc:
        _handle_common(exc)
    return ProjectRead.model_validate(project)


@router.post("/{project_id}/approve-prompt", response_model=ProjectRead)
@limiter.limit("10/minute")
async def approve_prompt(
    request: Request,
    project_id: int,
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(_service),
) -> ProjectRead:
    try:
        project = await service.approve_prompt(project_id, current_user.id)
    except Exception as exc:
        _handle_common(exc)
    return ProjectRead.model_validate(project)


# ----------------------------------------------------------------------
# Video phase
# ----------------------------------------------------------------------

@router.post("/{project_id}/generate-video", response_model=ProjectRead)
@limiter.limit("10/minute")
async def generate_video(
    request: Request,
    project_id: int,
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(_service),
) -> ProjectRead:
    try:
        project = await service.generate_video(project_id, current_user.id)
    except Exception as exc:
        _handle_common(exc)
    return ProjectRead.model_validate(project)


@router.post("/{project_id}/approve-video", response_model=ProjectRead)
@limiter.limit("10/minute")
async def approve_video(
    request: Request,
    project_id: int,
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(_service),
) -> ProjectRead:
    try:
        project = await service.approve_video(project_id, current_user.id)
    except Exception as exc:
        _handle_common(exc)
    return ProjectRead.model_validate(project)


@router.post("/{project_id}/reject-video", response_model=ProjectRead)
@limiter.limit("10/minute")
async def reject_video(
    request: Request,
    project_id: int,
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(_service),
) -> ProjectRead:
    try:
        project = await service.reject_video(project_id, current_user.id)
    except Exception as exc:
        _handle_common(exc)
    return ProjectRead.model_validate(project)


# ----------------------------------------------------------------------
# Metadata phase
# ----------------------------------------------------------------------

@router.post("/{project_id}/generate-metadata", response_model=ProjectRead)
@limiter.limit("10/minute")
async def generate_metadata(
    request: Request,
    project_id: int,
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(_service),
) -> ProjectRead:
    try:
        project = await service.generate_metadata(project_id, current_user.id)
    except Exception as exc:
        _handle_common(exc)
    return ProjectRead.model_validate(project)


@router.post("/{project_id}/approve-metadata", response_model=ProjectRead)
async def approve_metadata(
    project_id: int,
    body: MetadataApprove,
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(_service),
) -> ProjectRead:
    try:
        project = await service.approve_metadata(
            project_id,
            current_user.id,
            body.edited_title,
            body.edited_description,
        )
    except Exception as exc:
        _handle_common(exc)
    return ProjectRead.model_validate(project)


@router.post("/{project_id}/finalize", response_model=ProjectRead)
@limiter.limit("10/minute")
async def finalize(
    request: Request,
    project_id: int,
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(_service),
) -> ProjectRead:
    try:
        project = await service.finalize(project_id, current_user.id)
    except Exception as exc:
        _handle_common(exc)
    return ProjectRead.model_validate(project)


# ----------------------------------------------------------------------
# Status / download / publishing
# ----------------------------------------------------------------------

@router.get("/{project_id}/generation-status", response_model=GenerationStatusRead)
async def get_generation_status(
    project_id: int,
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(_service),
) -> GenerationStatusRead:
    try:
        return await service.get_generation_status(project_id, current_user.id)
    except Exception as exc:
        _handle_common(exc)


@router.get("/{project_id}/download")
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


@router.post("/{project_id}/publish-youtube", response_model=YouTubePublishResponse)
async def publish_youtube(
    project_id: int,
    current_user: User = Depends(get_current_user),
    service: VideoService = Depends(_service),
) -> YouTubePublishResponse:
    try:
        result = await service.publish_youtube_stub(project_id, current_user.id)
    except Exception as exc:
        _handle_common(exc)
    return YouTubePublishResponse(**result)
