from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class ProjectCreate(BaseModel):
    topic: str

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Topic must be at least 3 characters")
        if len(v) > 500:
            raise ValueError("Topic must be at most 500 characters")
        return v


class PromptEdit(BaseModel):
    edited_prompt: str

    @field_validator("edited_prompt")
    @classmethod
    def validate_edited_prompt(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 1:
            raise ValueError("edited_prompt cannot be empty")
        if len(v) > 5000:
            raise ValueError("edited_prompt must be at most 5000 characters")
        return v


class MetadataApprove(BaseModel):
    edited_title: str | None = None
    edited_description: str | None = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class GenerationStepRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prompt_used: str
    video_url: str | None
    celery_task_id: str | None
    is_approved: bool
    created_at: datetime


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topic: str

    generated_prompt: str | None
    edited_prompt: str | None
    prompt_status: str

    video_url: str | None
    video_status: str

    title: str | None
    description: str | None
    metadata_status: str

    workflow_status: str
    error_message: str | None

    created_at: datetime
    updated_at: datetime

    generation_steps: list[GenerationStepRead]


class ProjectListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topic: str
    workflow_status: str
    prompt_status: str
    video_status: str
    metadata_status: str
    created_at: datetime
    updated_at: datetime


class GenerationStatusRead(BaseModel):
    workflow_status: str
    video_status: str
    video_url: str | None
    celery_task_id: str | None
    error_message: str | None


class YouTubePublishResponse(BaseModel):
    message: str
    youtube_url: str | None
