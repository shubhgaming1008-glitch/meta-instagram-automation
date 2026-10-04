"""
Link and LinkClick models for the link manager.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Link(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "links"

    ig_account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("instagram_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    campaign_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True
    )
    automation_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("automations.id", ondelete="SET NULL"), nullable=True
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    destination_url: Mapped[str] = mapped_column(Text, nullable=False)

    # Protected link config
    is_protected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Opaque token for the /unlock/{token} URL
    token: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    # Whether the destination URL is revealed only after unlock
    requires_follow: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # UTM parameters
    utm_params: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    # Restrictions
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    max_clicks: Mapped[Optional[int]] = mapped_column(Integer)
    is_one_time_per_user: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Status
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Analytics (denormalized counters)
    total_clicks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unique_clicks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_unlocks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_click_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    campaign: Mapped[Optional["Campaign"]] = relationship("Campaign", back_populates="links")  # noqa
    clicks: Mapped[list["LinkClick"]] = relationship(
        "LinkClick", back_populates="link", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Link {self.name} [{self.status}]>"


class LinkClick(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "link_clicks"

    link_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("links.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contact_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True
    )
    campaign_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True
    )
    automation_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("automations.id", ondelete="SET NULL"), nullable=True
    )

    # Privacy-safe tracking (hashed IP, not raw)
    ip_hash: Mapped[Optional[str]] = mapped_column(String(64))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))

    clicked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    unlocked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_unique: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    link: Mapped["Link"] = relationship("Link", back_populates="clicks")
    contact: Mapped[Optional["Contact"]] = relationship("Contact", back_populates="link_clicks")  # noqa
