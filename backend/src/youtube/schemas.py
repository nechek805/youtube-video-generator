from datetime import datetime

from pydantic import BaseModel


class YouTubeAccountRead(BaseModel):
    """Returned to the frontend to show connection status."""

    id: int
    channel_id: str | None
    channel_name: str | None
    channel_thumbnail: str | None
    connected_at: datetime

    model_config = {"from_attributes": True}


class YouTubePublishRequest(BaseModel):
    """Optional overrides when publishing a project to YouTube."""

    title: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    # privacy: public | unlisted | private
    privacy: str = "public"


class YouTubePublishResult(BaseModel):
    youtube_video_id: str
    youtube_url: str
    title: str
