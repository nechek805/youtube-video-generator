from dataclasses import dataclass


@dataclass
class YouTubeUploadResult:
    youtube_video_id: str | None
    youtube_url: str | None
    message: str


class YouTubeUploader:
    """Stub for YouTube publishing.

    Future implementation will:
      1. Accept per-user OAuth credentials via a separate auth flow.
      2. Upload a local or remote video file via the YouTube Data API v3.
      3. Set title, description, tags, category, and thumbnail.
      4. Return the published video URL.

    Until then, ``upload`` is a no-op that returns a placeholder response.
    """

    _STUB_MESSAGE = (
        "YouTube publishing is not yet implemented. "
        "Your video is ready for manual upload."
    )

    async def upload(
        self,
        *,
        video_url: str,
        title: str,
        description: str,
    ) -> YouTubeUploadResult:
        return YouTubeUploadResult(
            youtube_video_id=None,
            youtube_url=None,
            message=self._STUB_MESSAGE,
        )
