from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base

if TYPE_CHECKING:
    from src.user.models import User


class YouTubeAccount(Base):
    """Stores per-user Google OAuth tokens for YouTube uploads.

    One user can have at most one connected YouTube account
    (unique constraint on user_id).  The access_token expires
    after ~1 hour; the refresh_token is long-lived and is used
    to obtain a new access_token automatically.
    """

    __tablename__ = "youtube_accounts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # OAuth tokens
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    token_expiry: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Channel info (populated on first connect)
    channel_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    channel_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    channel_thumbnail: Mapped[str | None] = mapped_column(Text, nullable=True)

    connected_at: Mapped[datetime] = mapped_column(
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
