"""
Automation and AutomationVersion models.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Automation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automations"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ig_account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("instagram_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    campaign_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True, index=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Status: draft | active | paused | archived
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False, index=True)

    # Trigger configuration
    # trigger_type: comment | dm_keyword | story_reply | story_mention | live_comment | webhook | manual | api
    trigger_type: Mapped[str] = mapped_column(String(100), nullable=False)
    trigger_config: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    # Version management
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    current_flow: Mapped[Optional[dict]] = mapped_column(JSON)  # Snapshot of current flow

    # Timing
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Analytics counters (denormalized)
    total_runs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_dms_sent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_comments_replied: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_link_clicks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_button_clicks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Settings
    is_test_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    prevent_duplicate_dm: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    duplicate_window_hours: Mapped[int] = mapped_column(Integer, default=24, nullable=False)

    # Relationships
    ig_account: Mapped["InstagramAccount"] = relationship(  # noqa
        "InstagramAccount", back_populates="automations"
    )
    campaign: Mapped[Optional["Campaign"]] = relationship(  # noqa
        "Campaign", back_populates="automations"
    )
    nodes: Mapped[list["WorkflowNode"]] = relationship(  # noqa
        "WorkflowNode", back_populates="automation", cascade="all, delete-orphan"
    )
    edges: Mapped[list["WorkflowEdge"]] = relationship(  # noqa
        "WorkflowEdge", back_populates="automation", cascade="all, delete-orphan"
    )
    versions: Mapped[list["AutomationVersion"]] = relationship(  # noqa
        "AutomationVersion", back_populates="automation", cascade="all, delete-orphan"
    )
    jobs: Mapped[list["Job"]] = relationship(  # noqa
        "Job", back_populates="automation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Automation {self.name} [{self.status}]>"


class AutomationVersion(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "automation_versions"

    automation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("automations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)  # Full flow snapshot
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    change_summary: Mapped[Optional[str]] = mapped_column(String(500))

    automation: Mapped["Automation"] = relationship(  # noqa
        "Automation", back_populates="versions"
    )
