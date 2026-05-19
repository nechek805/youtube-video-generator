import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.core.config import config


@dataclass
class VideoResult:
    """Outcome of a video generation request.

    Synchronous providers (mock) return with ``is_complete=True`` and a
    ``video_url`` set. Asynchronous providers may return with
    ``is_complete=False`` and only a ``provider_job_id`` — the workflow then
    leaves the project in ``VideoStatus.GENERATING`` and a background worker
    (or a follow-up call to ``check_status``) finishes the job later.
    """

    video_url: str | None
    provider: str
    provider_job_id: str | None = None
    is_complete: bool = True


class VideoGeneratorService(ABC):
    """Provider-agnostic interface for video generation.

    Concrete implementations should be added for Runway, Pika, Luma, Kling,
    etc. The mock implementation here is sufficient for MVP development.
    """

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


class MockVideoGenerator(VideoGeneratorService):
    """In-process placeholder that returns a fake CDN URL without calling any external service.

    Use during development. Simulates a small delay so the UI can show a
    loading state, but does not actually produce a video file.
    """

    def __init__(
        self,
        *,
        cdn_base: str | None = None,
        delay_seconds: float = 2.0,
    ) -> None:
        self._cdn_base = cdn_base or config.get_mock_video_cdn_base()
        self._delay = delay_seconds

    async def generate(
        self,
        *,
        prompt: str,
        project_id: int,
        step_id: int,
    ) -> VideoResult:
        await asyncio.sleep(self._delay)
        url = f"{self._cdn_base}/{step_id}.mp4"
        return VideoResult(
            video_url=url,
            provider="mock",
            provider_job_id=f"mock-{step_id}",
            is_complete=True,
        )


def get_video_generator() -> VideoGeneratorService:
    """Factory returning the currently-active video generator.

    Swap providers by changing the return value here. The rest of the
    workflow depends only on the ``VideoGeneratorService`` interface, so no
    other code needs to change.
    """
    return MockVideoGenerator()
