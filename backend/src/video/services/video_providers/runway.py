from .base import VideoProvider, VideoResult


class RunwayProvider(VideoProvider):
    """Placeholder for Runway video generation.

    Future: integrate with the Runway Gen-3 API.
      docs: https://docs.dev.runwayml.com/
    """

    name = "runway"

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
            "Runway provider not yet integrated. "
            "Set VIDEO_PROVIDER=mock for development."
        )
