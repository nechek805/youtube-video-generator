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
from src.video.services.video_generator import get_video_generator
from src.video.services.youtube import YouTubeUploader
from src.video.workflow import build_workflow_graph


def _now() -> datetime:
    return datetime.now(timezone.utc)


class VideoService:
    """Thin orchestration layer over the LangGraph workflow.

    Each mutating method:
      1. Calls ``_ensure_owner`` (raises ProjectNotFound / ProjectNotOwnedByUser).
      2. Guards the current ``workflow_status`` and the relevant phase status;
         raises ``InvalidProjectStatus`` if the action isn't valid here.
      3. Either:
           a. Invokes the graph with an action descriptor (for LLM /
              generation / phase transitions), OR
           b. Writes directly via the repository (for trivial edits and
              project creation).
      4. Returns the freshly reloaded project (nodes persist their own
         writes during the invocation).
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = VideoRepository(db)
        self.llm = LLMService()
        self.video_gen = get_video_generator()
        self.youtube = YouTubeUploader()
        self.graph = build_workflow_graph(
            repo=self.repo,
            llm=self.llm,
            video_gen=self.video_gen,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _ensure_owner(self, project_id: int, user_id: int) -> VideoProject:
        project = await self.repo.get_project_by_id(project_id)
        if project is None:
            raise ProjectNotFound(project_id)
        if project.user_id != user_id:
            raise ProjectNotOwnedByUser(project_id)
        return project

    def _guard_prompt_ready(self, project: VideoProject) -> None:
        if (
            project.workflow_status != WorkflowStatus.PROMPT
            or project.prompt_status != PromptStatus.READY
        ):
            raise InvalidProjectStatus(
                current=f"workflow={project.workflow_status.value}, prompt={project.prompt_status.value}",
                required=f"workflow={WorkflowStatus.PROMPT.value}, prompt={PromptStatus.READY.value}",
            )

    def _guard_prompt_phase(self, project: VideoProject) -> None:
        """Allow generate-prompt at any prompt_status while in PROMPT phase."""
        if project.workflow_status != WorkflowStatus.PROMPT:
            raise InvalidProjectStatus(
                current=f"workflow={project.workflow_status.value}",
                required=f"workflow={WorkflowStatus.PROMPT.value}",
            )

    def _guard_video_phase(self, project: VideoProject) -> None:
        """Allow generate-video at any video_status while in VIDEO phase."""
        if project.workflow_status != WorkflowStatus.VIDEO:
            raise InvalidProjectStatus(
                current=f"workflow={project.workflow_status.value}",
                required=f"workflow={WorkflowStatus.VIDEO.value}",
            )

    def _guard_video_ready(self, project: VideoProject) -> None:
        if (
            project.workflow_status != WorkflowStatus.VIDEO
            or project.video_status != VideoStatus.READY
        ):
            raise InvalidProjectStatus(
                current=f"workflow={project.workflow_status.value}, video={project.video_status.value}",
                required=f"workflow={WorkflowStatus.VIDEO.value}, video={VideoStatus.READY.value}",
            )

    def _guard_metadata_phase(self, project: VideoProject) -> None:
        if project.workflow_status != WorkflowStatus.METADATA:
            raise InvalidProjectStatus(
                current=f"workflow={project.workflow_status.value}",
                required=f"workflow={WorkflowStatus.METADATA.value}",
            )

    def _guard_metadata_ready(self, project: VideoProject) -> None:
        if (
            project.workflow_status != WorkflowStatus.METADATA
            or project.metadata_status != MetadataStatus.READY
        ):
            raise InvalidProjectStatus(
                current=f"workflow={project.workflow_status.value}, metadata={project.metadata_status.value}",
                required=f"workflow={WorkflowStatus.METADATA.value}, metadata={MetadataStatus.READY.value}",
            )

    def _guard_completed(self, project: VideoProject) -> None:
        if project.workflow_status != WorkflowStatus.COMPLETED:
            raise InvalidProjectStatus(
                current=project.workflow_status.value,
                required=WorkflowStatus.COMPLETED.value,
            )

    async def _reload(self, project_id: int) -> VideoProject:
        project = await self.repo.get_project_by_id(project_id)
        if project is None:
            raise ProjectNotFound(project_id)
        return project

    # ------------------------------------------------------------------
    # Read-only
    # ------------------------------------------------------------------

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
        self._guard_completed(project)
        if not project.video_url:
            raise VideoGenerationFailed("No video URL found for completed project")
        return project.video_url

    # ------------------------------------------------------------------
    # Creation (no graph)
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
        return await self._reload(project.id)

    # ------------------------------------------------------------------
    # Prompt phase
    # ------------------------------------------------------------------

    async def generate_prompt(self, project_id: int, user_id: int) -> VideoProject:
        project = await self._ensure_owner(project_id, user_id)
        self._guard_prompt_phase(project)
        await self.graph.ainvoke({
            "project_id": project.id,
            "action": "generate_prompt",
        })
        return await self._reload(project.id)

    async def edit_prompt(
        self, project_id: int, user_id: int, edited_prompt: str
    ) -> VideoProject:
        project = await self._ensure_owner(project_id, user_id)
        self._guard_prompt_ready(project)
        project.edited_prompt = edited_prompt.strip()
        project.updated_at = _now()
        await self.repo.update_project(project)
        logger.info("Prompt edited for project %d", project.id)
        return await self._reload(project.id)

    async def approve_prompt(self, project_id: int, user_id: int) -> VideoProject:
        project = await self._ensure_owner(project_id, user_id)
        self._guard_prompt_ready(project)
        await self.graph.ainvoke({
            "project_id": project.id,
            "action": "approve_prompt",
        })
        return await self._reload(project.id)

    # ------------------------------------------------------------------
    # Video phase
    # ------------------------------------------------------------------

    async def generate_video(self, project_id: int, user_id: int) -> VideoProject:
        project = await self._ensure_owner(project_id, user_id)
        self._guard_video_phase(project)
        await self.graph.ainvoke({
            "project_id": project.id,
            "action": "generate_video",
        })
        return await self._reload(project.id)

    async def approve_video(self, project_id: int, user_id: int) -> VideoProject:
        project = await self._ensure_owner(project_id, user_id)
        self._guard_video_ready(project)
        await self.graph.ainvoke({
            "project_id": project.id,
            "action": "approve_video",
        })
        return await self._reload(project.id)

    async def reject_video(self, project_id: int, user_id: int) -> VideoProject:
        project = await self._ensure_owner(project_id, user_id)
        self._guard_video_ready(project)
        await self.graph.ainvoke({
            "project_id": project.id,
            "action": "reject_video",
        })
        return await self._reload(project.id)

    # ------------------------------------------------------------------
    # Metadata phase
    # ------------------------------------------------------------------

    async def generate_metadata(self, project_id: int, user_id: int) -> VideoProject:
        project = await self._ensure_owner(project_id, user_id)
        self._guard_metadata_phase(project)
        await self.graph.ainvoke({
            "project_id": project.id,
            "action": "generate_metadata",
        })
        return await self._reload(project.id)

    async def approve_metadata(
        self,
        project_id: int,
        user_id: int,
        edited_title: str | None,
        edited_description: str | None,
    ) -> VideoProject:
        project = await self._ensure_owner(project_id, user_id)
        self._guard_metadata_ready(project)
        title = (edited_title or "").strip()
        description = (edited_description or "").strip()
        if title:
            project.title = title
        if description:
            project.description = description
        project.updated_at = _now()
        await self.repo.update_project(project)
        logger.info("Metadata edits saved for project %d", project.id)
        return await self._reload(project.id)

    async def finalize(self, project_id: int, user_id: int) -> VideoProject:
        project = await self._ensure_owner(project_id, user_id)
        self._guard_metadata_ready(project)
        await self.graph.ainvoke({
            "project_id": project.id,
            "action": "finalize",
        })
        return await self._reload(project.id)

    # ------------------------------------------------------------------
    # YouTube publishing (stub)
    # ------------------------------------------------------------------

    async def publish_youtube_stub(self, project_id: int, user_id: int) -> dict:
        project = await self._ensure_owner(project_id, user_id)
        self._guard_completed(project)
        result = await self.youtube.upload(
            video_url=project.video_url or "",
            title=project.title or "",
            description=project.description or "",
        )
        return {"message": result.message, "youtube_url": result.youtube_url}
