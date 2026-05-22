from .base import VideoProvider, VideoResult


class PikaProvider(VideoProvider):
    """Placeholder for Pika Labs video generation.

    Future: integrate with the Pika API.
      docs: https://pika.art/
    """

    name = "pika"

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
            "Pika provider not yet integrated. "
            "Set VIDEO_PROVIDER=mock for development."
        )
