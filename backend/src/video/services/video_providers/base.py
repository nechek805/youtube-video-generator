from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class VideoResult:
    """Outcome of a video generation request.

    Synchronous providers (mock) return with ``is_complete=True`` and a
    ``video_url`` set. Asynchronous providers may return with
    ``is_complete=False`` and only a ``provider_job_id`` -- the workflow then
    leaves the project in ``VideoStatus.GENERATING`` and a background worker
    (or a follow-up call to ``check_status``) finishes the job later.
    """

    video_url: str | None
    provider: str
    provider_job_id: str | None = None
    is_complete: bool = True


class VideoProvider(ABC):
    """Provider-agnostic interface for video generation.

    Concrete subclasses should set ``name`` and implement ``generate``. If the
    provider is asynchronous (job-based), also implement ``check_status``.
    """

    name: str = "base"

    @abstractmethod
    async def generate(
        self,
        *,
        prompt: str,
        project_id: int,
        step_id: int,
    ) -> VideoResult:
        """Start a generation job.

        For sync providers, blocks until the video is ready and returns the
        URL. For async providers, kicks off the job and returns immediately
        with ``is_complete=False`` and a ``provider_job_id`` that can be
        polled via ``check_status``.
        """

    async def check_status(self, provider_job_id: str) -> VideoResult:
        """Poll the provider for an async job. Override for async providers."""
        raise NotImplementedError(
            f"{type(self).__name__} does not support async polling"
        )
