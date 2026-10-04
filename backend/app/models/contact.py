"""
Contact model — Instagram users who have interacted.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Contact(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "contacts"

    ig_account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("instagram_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Instagram's IGSID (unique per user-business pair)
    ig_user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255))
    profile_picture_url: Mapped[Optional[str]] = mapped_column(Text)

    # Collected voluntarily
    email: Mapped[Optional[str]] = mapped_column(String(255), index=True)

    # Interaction tracking
    first_interaction_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_interaction_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_dm_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Status
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    opted_out: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Custom metadata (arbitrary key/value from automations)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, default=dict)

    # Relationships
    ig_account: Mapped["InstagramAccount"] = relationship(  # noqa
        "InstagramAccount", back_populates="contacts"
    )
    tags: Mapped[list["ContactTag"]] = relationship(  # noqa
        "ContactTag", back_populates="contact", cascade="all, delete-orphan"
    )
    messages: Mapped[list["Message"]] = relationship(  # noqa
        "Message", back_populates="contact", cascade="all, delete-orphan"
    )
    link_clicks: Mapped[list["LinkClick"]] = relationship(  # noqa
        "LinkClick", back_populates="contact"
    )
    jobs: Mapped[list["Job"]] = relationship(  # noqa
        "Job", back_populates="contact"
    )

    def __repr__(self) -> str:
        return f"<Contact @{self.username or self.ig_user_id}>"
