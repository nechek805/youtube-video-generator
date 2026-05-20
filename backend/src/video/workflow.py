"""LangGraph workflow for the YouTube video generator.

A single compiled graph with seven nodes covers the full producer flow:

    generate_prompt -> wait_for_prompt_approval
    generate_video -> wait_for_video_approval
    generate_metadata -> wait_for_metadata_approval
    finalize_project

The frontend controls every transition explicitly: each user HTTP request
invokes the graph once with a specific action, the conditional router at
START dispatches it to the right node, and the graph runs to END. Each
"doing" node persists its outputs to the database before yielding control,
so workflow progress is durable across requests and process restarts -- the
database is the source of truth, not in-memory graph state.

The "wait" nodes do double duty: they are terminal parks AND, when entered
as a phase transition (from a different workflow_status), they initialize
the next phase's status to PENDING. This lets approve_prompt / approve_video
be routed straight to the corresponding wait node without a separate
"transition" node.
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
from src.video.services.video_generator import VideoGeneratorService


WorkflowAction = Literal[
    "generate_prompt",    # runs LLM (also serves as "regenerate")
    "approve_prompt",     # phase transition PROMPT -> VIDEO
    "generate_video",     # runs video generator
    "approve_video",      # phase transition VIDEO -> METADATA
    "reject_video",       # phase transition VIDEO -> PROMPT
    "generate_metadata",  # runs metadata LLM
    "finalize",           # phase transition METADATA -> COMPLETED
]


class WorkflowState(TypedDict, total=False):
    """State carried through the graph.

    ``project_id`` and ``action`` are always set. The graph reads other
    fields from the database via the repo -- the state itself is minimal.
    """

    project_id: int
    action: WorkflowAction


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
    AsyncSession. This is cheap -- graph construction is pure Python with no
    IO.
    """

    # ------------------------------------------------------------------
    # Nodes
    # ------------------------------------------------------------------

    async def generate_prompt(state: WorkflowState) -> WorkflowState:
        project = await repo.get_project_by_id(state["project_id"])
        if project is None:
            raise VideoGenerationFailed(f"Project {state['project_id']} not found")

        project.prompt_status = PromptStatus.PENDING
        project.error_message = None
        project.updated_at = _now()
        await repo.update_project(project)

        try:
            prompt_text = await llm.generate_video_prompt(project.topic)
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
        """Run the video generator. Assumes workflow_status is already VIDEO."""
        project = await repo.get_project_by_id(state["project_id"])
        if project is None:
            raise VideoGenerationFailed(f"Project {state['project_id']} not found")

        active_prompt = project.edited_prompt or project.generated_prompt
        if not active_prompt:
            project.video_status = VideoStatus.FAILED
            project.workflow_status = WorkflowStatus.FAILED
            project.error_message = "No prompt available for video generation"
            project.updated_at = _now()
            await repo.update_project(project)
            raise VideoGenerationFailed(project.error_message)

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
            # Async provider -- the project stays in GENERATING until a
            # background worker (or a follow-up status check) finishes it.
            logger.info(
                "Video generation dispatched for project %d (provider=%s, job=%s)",
                project.id, result.provider, result.provider_job_id,
            )

        project.updated_at = _now()
        await repo.update_project(project)
        return state

    async def wait_for_video_approval(state: WorkflowState) -> WorkflowState:
        """Park the project in VIDEO phase.

        Triggered by ``"approve_prompt"`` (transition from PROMPT) or as the
        terminal of the ``generate_video`` path. When entering from a
        different workflow_status, initializes video_status to PENDING.
        """
        project = await repo.get_project_by_id(state["project_id"])
        if project is None:
            return state

        if project.workflow_status != WorkflowStatus.VIDEO:
            # Phase transition PROMPT -> VIDEO (via approve_prompt)
            project.workflow_status = WorkflowStatus.VIDEO
            project.video_status = VideoStatus.PENDING
            project.video_url = None
            project.error_message = None
            project.updated_at = _now()
            await repo.update_project(project)
        return state

    async def reject_video(state: WorkflowState) -> WorkflowState:
        """User rejected the video -- reset video phase and return to prompt review."""
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
        """Run the metadata LLM. Assumes workflow_status is already METADATA."""
        project = await repo.get_project_by_id(state["project_id"])
        if project is None:
            raise VideoGenerationFailed(f"Project {state['project_id']} not found")

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
        """Park the project in METADATA phase.

        Triggered by ``"approve_video"`` (transition from VIDEO) or as the
        terminal of the ``generate_metadata`` path. When entering from a
        different workflow_status, initializes metadata_status to PENDING
        and marks the latest video step as approved.
        """
        project = await repo.get_project_by_id(state["project_id"])
        if project is None:
            return state

        if project.workflow_status != WorkflowStatus.METADATA:
            # Phase transition VIDEO -> METADATA (via approve_video)
            project.workflow_status = WorkflowStatus.METADATA
            project.metadata_status = MetadataStatus.PENDING
            project.title = None
            project.description = None
            project.error_message = None

            latest = await repo.get_latest_step(project.id)
            if latest:
                latest.is_approved = True
                await repo.update_step(latest)

            project.updated_at = _now()
            await repo.update_project(project)
        return state

    async def finalize_project(state: WorkflowState) -> WorkflowState:
        """Transition the project to COMPLETED.

        Edits to title/description are saved by the ``approve_metadata``
        service method (which bypasses the graph), so this node only does
        the final state transition.
        """
        project = await repo.get_project_by_id(state["project_id"])
        if project is None:
            raise VideoGenerationFailed(f"Project {state['project_id']} not found")

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
        if action == "generate_prompt":
            return "generate_prompt"
        if action == "approve_prompt":
            return "wait_for_video_approval"
        if action == "generate_video":
            return "generate_video"
        if action == "approve_video":
            return "wait_for_metadata_approval"
        if action == "reject_video":
            return "reject_video"
        if action == "generate_metadata":
            return "generate_metadata"
        if action == "finalize":
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

    # Single conditional router from START -- handles every user action.
    graph.add_conditional_edges(
        START,
        route_action,
        {
            "generate_prompt": "generate_prompt",
            "wait_for_video_approval": "wait_for_video_approval",
            "generate_video": "generate_video",
            "wait_for_metadata_approval": "wait_for_metadata_approval",
            "reject_video": "reject_video",
            "generate_metadata": "generate_metadata",
            "finalize_project": "finalize_project",
        },
    )

    # Phase 1: prompt
    graph.add_edge("generate_prompt", "wait_for_prompt_approval")
    graph.add_edge("wait_for_prompt_approval", END)

    # Phase 2: video -- reject loops back to prompt review
    graph.add_edge("generate_video", "wait_for_video_approval")
    graph.add_edge("wait_for_video_approval", END)
    graph.add_edge("reject_video", "wait_for_prompt_approval")

    # Phase 3: metadata
    graph.add_edge("generate_metadata", "wait_for_metadata_approval")
    graph.add_edge("wait_for_metadata_approval", END)

    # Phase 4: finalize
    graph.add_edge("finalize_project", END)

    return graph.compile()
