"""
Message and Conversation models.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Conversation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "conversations"

    ig_account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("instagram_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ig_conversation_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)

    # Status
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False)  # open, closed
    unread_count: Mapped[int] = mapped_column(default=0, nullable=False)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_message_preview: Mapped[Optional[str]] = mapped_column(String(500))
    is_automated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Internal notes
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    messages: Mapped[list["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Conversation {self.id}>"


class Message(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "messages"

    ig_account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("instagram_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    conversation_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True
    )
    automation_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("automations.id", ondelete="SET NULL"), nullable=True
    )

    # direction: in (received from user) | out (sent by automation or manually)
    direction: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    # message_type: text | buttons | quick_reply | image | template | comment_reply
    message_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Content stored as structured JSON (to support rich message types)
    content: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Meta's message ID for deduplication
    ig_message_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True)

    # Timestamps
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Status: pending | sent | delivered | read | failed
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    error: Mapped[Optional[str]] = mapped_column(Text)

    is_automated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    contact: Mapped["Contact"] = relationship("Contact", back_populates="messages")  # noqa
    conversation: Mapped[Optional["Conversation"]] = relationship(
        "Conversation", back_populates="messages"
    )

    def __repr__(self) -> str:
        return f"<Message {self.direction} [{self.status}]>"
