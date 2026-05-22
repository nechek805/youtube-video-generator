from .base import VideoProvider, VideoResult


class KlingProvider(VideoProvider):
    """Placeholder for Kling video generation.

    Future: integrate with the Kling AI API.
      docs: https://klingai.com/
    """

    name = "kling"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    async def generate(
        self,
        *,
        prompt: str,
        project_id: int,
        step_id: int,
    ) -> VideoResult:
        raise NotImplementedError(
            "Kling provider not yet integrated. "
            "Set VIDEO_PROVIDER=mock for development."
        )
