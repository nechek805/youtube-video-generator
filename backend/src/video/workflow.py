"""LangGraph workflow for the YouTube video generator.

A single compiled graph with seven nodes covers the full producer flow:

    generate_prompt → wait_for_prompt_approval
    generate_video → wait_for_video_approval
    generate_metadata → wait_for_metadata_approval
    finalize_project

Every user-driven action (create / approve / reject / regenerate / edit) is
expressed as a fresh invocation that enters at a conditional router and lands
on the right node. Each "doing" node persists its outputs to the database
before yielding control, so workflow progress is durable across requests and
process restarts — the database is the source of truth, not in-memory graph
state.
"""
from datetime import datetime, timezone
from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from src.logger import logger
from src.video.exceptions import VideoGenerationFailed
from src.video.models import (
    MetadataStatus,
    PromptStatus,
    VideoGenerationStep,
    VideoStatus,
    WorkflowStatus,
)
from src.video.repository import VideoRepository
from src.video.services.llm import LLMService
from src.video.services.video_providers import VideoProvider as VideoGeneratorService


WorkflowAction = Literal[
    "create",
    "regenerate_prompt",
    "approve_prompt",
    "approve_video",
    "reject_video",
    "approve_metadata",
]


class WorkflowState(TypedDict, total=False):
    """State carried through the graph.

    ``project_id`` and ``action`` are always set. Other keys are inputs for
    specific actions and are passed through as-is to the relevant nodes.
    """

    project_id: int
    action: WorkflowAction

    # Inputs for specific actions
    topic: str
    edited_prompt: str | None
    edited_title: str | None
    edited_description: str | None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def build_workflow_graph(
    *,
    repo: VideoRepository,
    llm: LLMService,
    video_gen: VideoGeneratorService,
):
    """Compile the unified video workflow graph with injected services.

    The graph is rebuilt per request because ``repo`` is bound to a single
    AsyncSession. This is cheap — graph construction is pure Python with no
    IO.
    """

    # ------------------------------------------------------------------
    # Nodes
    # ------------------------------------------------------------------

    async def generate_prompt(state: WorkflowState) -> WorkflowState:
        project = await repo.get_project_by_id(state["project_id"])
        if project is None:
            raise VideoGenerationFailed(f"Project {state['project_id']} not found")

        topic = state.get("topic") or project.topic

        project.prompt_status = PromptStatus.PENDING
        project.workflow_status = WorkflowStatus.PROMPT
        project.error_message = None
        project.updated_at = _now()
        await repo.update_project(project)

        try:
            prompt_text = await llm.generate_video_prompt(topic)
        except Exception as exc:
            project.prompt_status = PromptStatus.FAILED
            project.workflow_status = WorkflowStatus.FAILED
            project.error_message = str(exc)
            project.updated_at = _now()
            await repo.update_project(project)
            logger.exception("Prompt generation failed for project %d", project.id)
            raise VideoGenerationFailed(f"Prompt generation failed: {exc}") from exc

        if not prompt_text or len(prompt_text) < 50:
            project.prompt_status = PromptStatus.FAILED
            project.workflow_status = WorkflowStatus.FAILED
            project.error_message = "Generated prompt is too short or empty"
            project.updated_at = _now()
            await repo.update_project(project)
            raise VideoGenerationFailed(project.error_message)

        project.generated_prompt = prompt_text
        project.prompt_status = PromptStatus.READY
        project.updated_at = _now()
        await repo.update_project(project)
        logger.info("Prompt ready for project %d", project.id)
        return state

    async def wait_for_prompt_approval(state: WorkflowState) -> WorkflowState:
        """Park the project in PROMPT phase awaiting user action."""
        project = await repo.get_project_by_id(state["project_id"])
        if project and project.workflow_status != WorkflowStatus.PROMPT:
            project.workflow_status = WorkflowStatus.PROMPT
            project.updated_at = _now()
            await repo.update_project(project)
        return state

    async def generate_video(state: WorkflowState) -> WorkflowState:
        project = await repo.get_project_by_id(state["project_id"])
        if project is None:
            raise VideoGenerationFailed(f"Project {state['project_id']} not found")

        edited = (state.get("edited_prompt") or "").strip()
        if edited:
            project.edited_prompt = edited

        active_prompt = project.edited_prompt or project.generated_prompt
        if not active_prompt:
            project.video_status = VideoStatus.FAILED
            project.workflow_status = WorkflowStatus.FAILED
            project.error_message = "No prompt available for video generation"
            project.updated_at = _now()
            await repo.update_project(project)
            raise VideoGenerationFailed(project.error_message)

        project.workflow_status = WorkflowStatus.VIDEO
        project.video_status = VideoStatus.GENERATING
        project.video_url = None
        project.error_message = None
        project.updated_at = _now()
        await repo.update_project(project)

        step = VideoGenerationStep(
            project_id=project.id,
            prompt_used=active_prompt,
            created_at=_now(),
        )
        step = await repo.create_step(step)

        try:
            result = await video_gen.generate(
                prompt=active_prompt,
                project_id=project.id,
                step_id=step.id,
            )
        except Exception as exc:
            project.video_status = VideoStatus.FAILED
            project.workflow_status = WorkflowStatus.FAILED
            project.error_message = str(exc)
            project.updated_at = _now()
            await repo.update_project(project)
            logger.exception("Video generation failed for project %d", project.id)
            raise VideoGenerationFailed(f"Video generation failed: {exc}") from exc

        step.celery_task_id = result.provider_job_id
        step.video_url = result.video_url
        await repo.update_step(step)

        if result.is_complete and result.video_url:
            project.video_url = result.video_url
            project.video_status = VideoStatus.READY
            logger.info(
                "Video ready for project %d (provider=%s, step=%d)",
                project.id, result.provider, step.id,
            )
        else:
            # Async provider — the project stays in GENERATING until a
            # background worker (or a follow-up status check) finishes it.
            logger.info(
                "Video generation dispatched for project %d (provider=%s, job=%s)",
                project.id, result.provider, result.provider_job_id,
            )

        project.updated_at = _now()
        await repo.update_project(project)
        return state

    async def wait_for_video_approval(state: WorkflowState) -> WorkflowState:
        """Park the project in VIDEO phase awaiting user approval."""
        project = await repo.get_project_by_id(state["project_id"])
        if project and project.workflow_status != WorkflowStatus.VIDEO:
            project.workflow_status = WorkflowStatus.VIDEO
            project.updated_at = _now()
            await repo.update_project(project)
        return state

    async def reject_video(state: WorkflowState) -> WorkflowState:
        """User rejected the video — reset video phase and return to prompt review."""
        project = await repo.get_project_by_id(state["project_id"])
        if project is None:
            return state

        latest = await repo.get_latest_step(project.id)
        if latest:
            latest.is_approved = False
            await repo.update_step(latest)

        project.workflow_status = WorkflowStatus.PROMPT
        project.video_status = VideoStatus.PENDING
        project.video_url = None
        project.error_message = None
        project.updated_at = _now()
        await repo.update_project(project)
        logger.info("Video rejected for project %d, returned to PROMPT", project.id)
        return state

    async def generate_metadata(state: WorkflowState) -> WorkflowState:
        project = await repo.get_project_by_id(state["project_id"])
        if project is None:
            raise VideoGenerationFailed(f"Project {state['project_id']} not found")

        latest = await repo.get_latest_step(project.id)
        if latest:
            latest.is_approved = True
            await repo.update_step(latest)

        project.workflow_status = WorkflowStatus.METADATA
        project.metadata_status = MetadataStatus.PENDING
        project.error_message = None
        project.updated_at = _now()
        await repo.update_project(project)

        active_prompt = project.edited_prompt or project.generated_prompt or ""

        try:
            title = await llm.generate_youtube_title(active_prompt)
            description = await llm.generate_youtube_description(active_prompt, title)
        except Exception as exc:
            project.metadata_status = MetadataStatus.FAILED
            project.workflow_status = WorkflowStatus.FAILED
            project.error_message = str(exc)
            project.updated_at = _now()
            await repo.update_project(project)
            logger.exception("Metadata generation failed for project %d", project.id)
            raise VideoGenerationFailed(f"Metadata generation failed: {exc}") from exc

        project.title = title
        project.description = description
        project.metadata_status = MetadataStatus.READY
        project.updated_at = _now()
        await repo.update_project(project)
        logger.info("Metadata ready for project %d", project.id)
        return state

    async def wait_for_metadata_approval(state: WorkflowState) -> WorkflowState:
        """Park the project in METADATA phase awaiting final approval."""
        project = await repo.get_project_by_id(state["project_id"])
        if project and project.workflow_status != WorkflowStatus.METADATA:
            project.workflow_status = WorkflowStatus.METADATA
            project.updated_at = _now()
            await repo.update_project(project)
        return state

    async def finalize_project(state: WorkflowState) -> WorkflowState:
        project = await repo.get_project_by_id(state["project_id"])
        if project is None:
            raise VideoGenerationFailed(f"Project {state['project_id']} not found")

        edited_title = (state.get("edited_title") or "").strip()
        if edited_title:
            project.title = edited_title
        edited_description = (state.get("edited_description") or "").strip()
        if edited_description:
            project.description = edited_description

        project.workflow_status = WorkflowStatus.COMPLETED
        project.updated_at = _now()
        await repo.update_project(project)
        logger.info("Project %d completed", project.id)
        return state

    # ------------------------------------------------------------------
    # Conditional routing
    # ------------------------------------------------------------------

    def route_action(state: WorkflowState) -> str:
        action = state.get("action")
        if action in ("create", "regenerate_prompt"):
            return "generate_prompt"
        if action == "approve_prompt":
            return "generate_video"
        if action == "approve_video":
            return "generate_metadata"
        if action == "reject_video":
            return "reject_video"
        if action == "approve_metadata":
            return "finalize_project"
        raise ValueError(f"Unknown workflow action: {action!r}")

    # ------------------------------------------------------------------
    # Build & wire
    # ------------------------------------------------------------------

    graph = StateGraph(WorkflowState)

    graph.add_node("generate_prompt", generate_prompt)
    graph.add_node("wait_for_prompt_approval", wait_for_prompt_approval)
    graph.add_node("generate_video", generate_video)
    graph.add_node("wait_for_video_approval", wait_for_video_approval)
    graph.add_node("reject_video", reject_video)
    graph.add_node("generate_metadata", generate_metadata)
    graph.add_node("wait_for_metadata_approval", wait_for_metadata_approval)
    graph.add_node("finalize_project", finalize_project)

    # Single conditional router from START — handles every user action.
    graph.add_conditional_edges(
        START,
        route_action,
        {
            "generate_prompt": "generate_prompt",
            "generate_video": "generate_video",
            "generate_metadata": "generate_metadata",
            "reject_video": "reject_video",
            "finalize_project": "finalize_project",
        },
    )

    # Phase 1: prompt
    graph.add_edge("generate_prompt", "wait_for_prompt_approval")
    graph.add_edge("wait_for_prompt_approval", END)

    # Phase 2: video — reject loops back to prompt review
    graph.add_edge("generate_video", "wait_for_video_approval")
    graph.add_edge("wait_for_video_approval", END)
    graph.add_edge("reject_video", "wait_for_prompt_approval")

    # Phase 3: metadata
    graph.add_edge("generate_metadata", "wait_for_metadata_approval")
    graph.add_edge("wait_for_metadata_approval", END)

    # Phase 4: finalize
    graph.add_edge("finalize_project", END)

    return graph.compile()
