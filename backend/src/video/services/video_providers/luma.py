from .base import VideoProvider, VideoResult


class LumaProvider(VideoProvider):
    """Placeholder for Luma Dream Machine video generation.

    Future: integrate with the Luma Labs API.
      docs: https://lumalabs.ai/dream-machine/api
    """

    name = "luma"

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
            "Luma provider not yet integrated. "
            "Set VIDEO_PROVIDER=mock for development."
        )
