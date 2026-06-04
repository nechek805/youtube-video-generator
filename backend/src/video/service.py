from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.logger import logger
from src.video.exceptions import (
    InvalidProjectStatus,
    ProjectNotFound,
    ProjectNotOwnedByUser,
    VideoGenerationFailed,
)
from src.video.models import (
    MetadataStatus,
    PromptStatus,
    VideoProject,
    VideoStatus,
    WorkflowStatus,
)
from src.video.repository import VideoRepository
from src.video.schemas import GenerationStatusRead
from src.video.services.llm import LLMService
from src.video.services.video_providers import get_video_provider
from src.video.services.youtube import YouTubeUploader
from src.video.workflow import build_workflow_graph


def _now() -> datetime:
    return datetime.now(timezone.utc)


class VideoService:
    """Thin orchestration layer over the LangGraph workflow.

    Each public method:
      1. Ensures the caller owns the project (or creates a new one).
      2. Guards the project's current status against what the action expects.
      3. Invokes the workflow graph with an action descriptor.
      4. Returns the freshly-reloaded project (nodes persist their own writes).
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = VideoRepository(db)
        self.llm = LLMService()
        self.video_gen = get_video_provider()
        self.youtube = YouTubeUploader()
        self.graph = build_workflow_graph(
            repo=self.repo,
            llm=self.llm,
            video_gen=self.video_gen,
        )

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    async def _ensure_owner(self, project_id: int, user_id: int) -> VideoProject:
        project = await self.repo.get_project_by_id(project_id)
        if project is None:
            raise ProjectNotFound(project_id)
        if project.user_id != user_id:
            raise ProjectNotOwnedByUser(project_id)
        return project

    async def get_project(self, project_id: int, user_id: int) -> VideoProject:
        return await self._ensure_owner(project_id, user_id)

    async def list_projects(self, user_id: int) -> list[VideoProject]:
        return await self.repo.get_projects_by_user_id(user_id)

    async def get_generation_status(
        self, project_id: int, user_id: int
    ) -> GenerationStatusRead:
        project = await self._ensure_owner(project_id, user_id)
        latest = await self.repo.get_latest_step(project_id)
        return GenerationStatusRead(
            workflow_status=project.workflow_status.value,
            video_status=project.video_status.value,
            video_url=project.video_url,
            celery_task_id=latest.celery_task_id if latest else None,
            error_message=project.error_message,
        )

    async def get_download_info(self, project_id: int, user_id: int) -> str:
        project = await self._ensure_owner(project_id, user_id)
        if project.workflow_status != WorkflowStatus.COMPLETED:
            raise InvalidProjectStatus(
                current=project.workflow_status.value,
                required=WorkflowStatus.COMPLETED.value,
            )
        if not project.video_url:
            raise VideoGenerationFailed("No video URL found for completed project")
        return project.video_url

    # ------------------------------------------------------------------
    # Workflow actions
    # ------------------------------------------------------------------

    async def create_project(self, user_id: int, topic: str) -> VideoProject:
        project = VideoProject(
            user_id=user_id,
            topic=topic,
            workflow_status=WorkflowStatus.PROMPT,
            prompt_status=PromptStatus.PENDING,
            video_status=VideoStatus.PENDING,
            metadata_status=MetadataStatus.PENDING,
            created_at=_now(),
            updated_at=_now(),
        )
        project = await self.repo.create_project(project)
        logger.info("Project %d created (user=%d topic=%r)", project.id, user_id, topic)

        await self.graph.ainvoke({
            "project_id": project.id,
            "action": "create",
            "topic": topic,
        })
        return await self.repo.get_project_by_id(project.id)

    async def regenerate_prompt(
        self, project_id: int, user_id: int, instruction: str | None = None
    ) -> VideoProject:
        project = await self._ensure_owner(project_id, user_id)
        if project.workflow_status != WorkflowStatus.PROMPT:
            raise InvalidProjectStatus(
                current=project.workflow_status.value,
                required=WorkflowStatus.PROMPT.value,
            )
        state: dict = {
            "project_id": project.id,
            "action": "regenerate_prompt",
        }
        if instruction:
            state["instruction"] = instruction
        await self.graph.ainvoke(state)
        return await self.repo.get_project_by_id(project.id)

    async def save_prompt(
        self, project_id: int, user_id: int, edited_prompt: str
    ) -> VideoProject:
        """Persist an edited prompt without starting video generation."""
        project = await self._ensure_owner(project_id, user_id)
        if project.workflow_status != WorkflowStatus.PROMPT:
            raise InvalidProjectStatus(
                current=project.workflow_status.value,
                required=WorkflowStatus.PROMPT.value,
            )
        project.edited_prompt = edited_prompt
        project.updated_at = _now()
        await self.repo.update_project(project)
        return await self.repo.get_project_by_id(project.id)

    async def approve_prompt(
        self, project_id: int, user_id: int, edited_prompt: str | None
    ) -> VideoProject:
        project = await self._ensure_owner(project_id, user_id)
        if (
            project.workflow_status != WorkflowStatus.PROMPT
            or project.prompt_status != PromptStatus.READY
        ):
            raise InvalidProjectStatus(
                current=f"workflow={project.workflow_status.value}, prompt={project.prompt_status.value}",
                required=f"workflow={WorkflowStatus.PROMPT.value}, prompt={PromptStatus.READY.value}",
            )
        await self.graph.ainvoke({
            "project_id": project.id,
            "action": "approve_prompt",
            "edited_prompt": edited_prompt,
        })
        return await self.repo.get_project_by_id(project.id)

    async def approve_video(
        self, project_id: int, user_id: int, approved: bool
    ) -> VideoProject:
        project = await self._ensure_owner(project_id, user_id)
        if (
            project.workflow_status != WorkflowStatus.VIDEO
            or project.video_status != VideoStatus.READY
        ):
            raise InvalidProjectStatus(
                current=f"workflow={project.workflow_status.value}, video={project.video_status.value}",
                required=f"workflow={WorkflowStatus.VIDEO.value}, video={VideoStatus.READY.value}",
            )
        await self.graph.ainvoke({
            "project_id": project.id,
            "action": "approve_video" if approved else "reject_video",
        })
        return await self.repo.get_project_by_id(project.id)

    async def approve_metadata(
        self,
        project_id: int,
        user_id: int,
        edited_title: str | None,
        edited_description: str | None,
    ) -> VideoProject:
        project = await self._ensure_owner(project_id, user_id)
        if (
            project.workflow_status != WorkflowStatus.METADATA
            or project.metadata_status != MetadataStatus.READY
        ):
            raise InvalidProjectStatus(
                current=f"workflow={project.workflow_status.value}, metadata={project.metadata_status.value}",
                required=f"workflow={WorkflowStatus.METADATA.value}, metadata={MetadataStatus.READY.value}",
            )
        await self.graph.ainvoke({
            "project_id": project.id,
            "action": "approve_metadata",
            "edited_title": edited_title,
            "edited_description": edited_description,
        })
        return await self.repo.get_project_by_id(project.id)

    async def add_part(self, project_id: int, user_id: int) -> VideoProject:
        """Start generating the prompt for the next video part (max 3 parts)."""
        project = await self._ensure_owner(project_id, user_id)

        # Must be in VIDEO/READY and have already saved the current part.
        saved_parts = len(project.parts)
        if (
            project.workflow_status != WorkflowStatus.VIDEO
            or project.video_status != VideoStatus.READY
            or saved_parts < project.parts_count  # current part not saved yet
        ):
            raise InvalidProjectStatus(
                current=f"workflow={project.workflow_status.value}, parts_saved={saved_parts}/{project.parts_count}",
                required="video approved and saved as part first",
            )
        if project.parts_count >= 3:
            raise InvalidProjectStatus(
                current=f"parts_count={project.parts_count}",
                required="parts_count < 3",
            )

        # Increment counter and clear current-part fields for the new part.
        project.parts_count += 1
        project.generated_prompt = None
        project.edited_prompt = None
        project.prompt_status = PromptStatus.PENDING
        project.video_url = None
        project.video_status = VideoStatus.PENDING
        project.error_message = None
        project.updated_at = _now()
        await self.repo.update_project(project)

        await self.graph.ainvoke({
            "project_id": project.id,
            "action": "add_part",
        })
        return await self.repo.get_project_by_id(project.id)

    async def finalize_parts(self, project_id: int, user_id: int) -> VideoProject:
        """Move from VIDEO (parts done) → METADATA generation."""
        project = await self._ensure_owner(project_id, user_id)

        saved_parts = len(project.parts)
        if (
            project.workflow_status != WorkflowStatus.VIDEO
            or project.video_status != VideoStatus.READY
            or saved_parts < project.parts_count
        ):
            raise InvalidProjectStatus(
                current=f"workflow={project.workflow_status.value}, parts_saved={saved_parts}/{project.parts_count}",
                required="all parts saved before finalizing",
            )

        await self.graph.ainvoke({
            "project_id": project.id,
            "action": "finalize_parts",
        })
        return await self.repo.get_project_by_id(project.id)

    # ------------------------------------------------------------------
    # YouTube publishing (stub)
    # ------------------------------------------------------------------

    async def publish_youtube_stub(self, project_id: int, user_id: int) -> dict:
        project = await self._ensure_owner(project_id, user_id)
        if project.workflow_status != WorkflowStatus.COMPLETED:
            raise InvalidProjectStatus(
                current=project.workflow_status.value,
                required=WorkflowStatus.COMPLETED.value,
            )
        video_urls = (
            [p.video_url for p in sorted(project.parts, key=lambda p: p.part_number)]
            if project.parts
            else [project.video_url or ""]
        )
        result = await self.youtube.upload(
            video_urls=video_urls,
            title=project.title or "",
            description=project.description or "",
        )
        return {"message": result.message, "youtube_url": result.youtube_url}
