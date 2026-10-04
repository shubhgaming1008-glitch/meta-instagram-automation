"""
WebhookEvent model — raw storage for deduplication and debugging.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import UUIDPrimaryKeyMixin


class WebhookEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "webhook_events"

    ig_account_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("instagram_accounts.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Meta's unique event identifier for deduplication
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    ig_event_id: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)

    # Raw payload stored for debugging (never exposes tokens)
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=False)

    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    error: Mapped[Optional[str]] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<WebhookEvent {self.event_type} [{self.ig_event_id}]>"
