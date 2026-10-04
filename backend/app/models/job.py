"""
Job and JobAttempt models — persistent automation execution queue.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDPrimaryKeyMixin


class Job(UUIDPrimaryKeyMixin, Base):
    """
    Represents a single automation execution instance.
    Status: pending | running | completed | failed | retrying | dead
    """
    __tablename__ = "jobs"

    automation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("automations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contact_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    trigger_event_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("webhook_events.id", ondelete="SET NULL"), nullable=True
    )

    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)
    current_node_id: Mapped[Optional[str]] = mapped_column(String(100))

    # Full execution context (node states, collected values, etc.)
    execution_context: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    # Idempotency key — prevents duplicate execution for same trigger+contact
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    # Timing
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Retry tracking
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    error: Mapped[Optional[str]] = mapped_column(Text)

    # Celery task ID for correlation
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(100))

    # Relationships
    automation: Mapped["Automation"] = relationship("Automation", back_populates="jobs")  # noqa
    contact: Mapped[Optional["Contact"]] = relationship("Contact", back_populates="jobs")  # noqa
    attempts: Mapped[list["JobAttempt"]] = relationship(
        "JobAttempt", back_populates="job", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Job {self.id} [{self.status}]>"


class JobAttempt(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "job_attempts"

    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    node_id: Mapped[Optional[str]] = mapped_column(String(100))

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    result: Mapped[Optional[dict]] = mapped_column(JSON)
    error: Mapped[Optional[str]] = mapped_column(Text)

    job: Mapped["Job"] = relationship("Job", back_populates="attempts")
