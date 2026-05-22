import asyncio

from src.core.config import config
from .base import VideoProvider, VideoResult


class MockVideoProvider(VideoProvider):
    """In-process placeholder that does not call any external service.

    Use during development. Simulates a small delay so the UI can show a
    loading state. Returns a ``video_url`` in one of two modes (set via
    ``MOCK_VIDEO_MODE``):

      - ``placeholder`` (default): ``{cdn_base}/{step_id}.mp4`` -- a fake
        CDN URL. Nothing is served at that address; the frontend video
        player will fail to load it. Useful for storage/state tests.
      - ``static``: ``{BASE_URL}/static/sample.mp4`` -- served by the
        StaticFiles mount in main.py. Drop a real MP4 at
        ``backend/static/sample.mp4`` to make the player work.
    """

    name = "mock"

    def __init__(
        self,
        *,
        cdn_base: str | None = None,
        delay_seconds: float = 2.0,
        mode: str | None = None,
    ) -> None:
        self._cdn_base = cdn_base or config.get_mock_video_cdn_base()
        self._delay = delay_seconds
        self._mode = (mode or config.get_mock_video_mode() or "placeholder").lower()

    def _build_url(self, step_id: int) -> str:
        if self._mode == "static":
            base = config.get_base_url() or "http://localhost:8000"
            return f"{base.rstrip('/')}/static/sample.mp4"
        return f"{self._cdn_base}/{step_id}.mp4"

    async def generate(
        self,
        *,
        prompt: str,
        project_id: int,
        step_id: int,
    ) -> VideoResult:
        await asyncio.sleep(self._delay)
        return VideoResult(
            video_url=self._build_url(step_id),
            provider="mock",
            provider_job_id=f"mock-{step_id}",
            is_complete=True,
        )
