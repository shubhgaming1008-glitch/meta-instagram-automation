"""
Campaign model — groups automations for unified tracking.
"""
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Campaign(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "campaigns"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ig_account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("instagram_accounts.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Analytics counters (denormalized for performance)
    total_triggers: Mapped[int] = mapped_column(default=0, nullable=False)
    total_dms_sent: Mapped[int] = mapped_column(default=0, nullable=False)
    total_link_clicks: Mapped[int] = mapped_column(default=0, nullable=False)

    # Relationships
    automations: Mapped[list["Automation"]] = relationship(  # noqa
        "Automation", back_populates="campaign"
    )
    links: Mapped[list["Link"]] = relationship(  # noqa
        "Link", back_populates="campaign"
    )

    def __repr__(self) -> str:
        return f"<Campaign {self.name}>"
