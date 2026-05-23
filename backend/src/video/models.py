from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.user.models import User


class WorkflowStatus(str, Enum):
    PROMPT = "PROMPT"
    VIDEO = "VIDEO"
    METADATA = "METADATA"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PromptStatus(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    FAILED = "FAILED"


class VideoStatus(str, Enum):
    PENDING = "PENDING"
    GENERATING = "GENERATING"
    READY = "READY"
    FAILED = "FAILED"


class MetadataStatus(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    FAILED = "FAILED"


def _enum(cls, name: str) -> SQLEnum:
    return SQLEnum(
        cls,
        values_callable=lambda e: [x.value for x in e],
        name=name,
    )


class VideoProject(Base):
    __tablename__ = "video_projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Input
    topic: Mapped[str] = mapped_column(Text, nullable=False)

    # Prompt phase
    generated_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    edited_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_status: Mapped[PromptStatus] = mapped_column(
        _enum(PromptStatus, "promptstatus"),
        nullable=False,
        default=PromptStatus.PENDING,
    )

    # Video phase
    video_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_status: Mapped[VideoStatus] = mapped_column(
        _enum(VideoStatus, "videostatus"),
        nullable=False,
        default=VideoStatus.PENDING,
    )

    # Metadata phase
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    metadata_status: Mapped[MetadataStatus] = mapped_column(
        _enum(MetadataStatus, "metadatastatus"),
        nullable=False,
        default=MetadataStatus.PENDING,
    )

    # Overall workflow
    workflow_status: Mapped[WorkflowStatus] = mapped_column(
        _enum(WorkflowStatus, "workflowstatus"),
        nullable=False,
        default=WorkflowStatus.PROMPT,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship()
    generation_steps: Mapped[list["VideoGenerationStep"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="VideoGenerationStep.created_at",
    )


class VideoGenerationStep(Base):
    __tablename__ = "video_generation_steps"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("video_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    prompt_used: Mapped[str] = mapped_column(Text, nullable=False)
    video_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    project: Mapped["VideoProject"] = relationship(back_populates="generation_steps")
