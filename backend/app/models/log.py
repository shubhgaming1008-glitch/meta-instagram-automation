"""
ExecutionLog model — human-readable event timeline for the Logs page.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import UUIDPrimaryKeyMixin


class ExecutionLog(UUIDPrimaryKeyMixin, Base):
    """
    Logs every significant automation event.
    Level: info | warning | error | failed | retrying
    Category: trigger | condition | message | link | follow_check | delay | tag | system
    """
    __tablename__ = "execution_logs"

    job_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    automation_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("automations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    contact_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    ig_account_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("instagram_accounts.id", ondelete="SET NULL"), nullable=True, index=True
    )

    level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    node_id: Mapped[Optional[str]] = mapped_column(String(100))
    node_type: Mapped[Optional[str]] = mapped_column(String(100))
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # API response or result metadata
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON)
    api_status_code: Mapped[Optional[int]] = mapped_column()
    retry_count: Mapped[Optional[int]] = mapped_column()
    final_state: Mapped[Optional[str]] = mapped_column(String(50))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:
        return f"<ExecutionLog [{self.level}] {self.message[:50]}>"
