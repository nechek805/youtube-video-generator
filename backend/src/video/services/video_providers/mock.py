import asyncio

from src.core.config import config
from .base import VideoProvider, VideoResult


class MockVideoProvider(VideoProvider):
    """In-process placeholder that does not call any external service.

    Use during development. Simulates a small delay so the UI can show a
    loading state. The returned ``video_url`` is either a fake CDN URL or
    a local ``/static/sample.mp4`` URL, depending on configuration -- the
    mode switch lives in commit 4 of this plan; for now this class always
    returns the CDN-style placeholder.
    """

    name = "mock"

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
