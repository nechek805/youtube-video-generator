from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum

from src.core.database import Base

if TYPE_CHECKING:
    from src.session.models import Session


class EmailStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    DEACTIVATED = "DEACTIVATED"
    BANNED = "BANNED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    email_status: Mapped[EmailStatus] = mapped_column(
        SQLEnum(
            EmailStatus,
            values_callable=lambda enum: [e.value for e in enum],
            name="emailstatus",
        ),
        default=EmailStatus.PENDING,
        nullable=False
    )

    sessions: Mapped[list["Session"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    email_confirmation_tokens: Mapped[list["EmailConfirmationToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class EmailConfirmationToken(Base):
    __tablename__ = "email_confirmation_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    hashed_token: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    user: Mapped["User"] = relationship()
