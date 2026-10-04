"""
Instagram Account model — connected via Meta OAuth.
Access tokens are encrypted at rest.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class InstagramAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "instagram_accounts"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Instagram-assigned identifiers
    ig_user_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    ig_username: Mapped[Optional[str]] = mapped_column(String(255))
    ig_name: Mapped[Optional[str]] = mapped_column(String(255))
    ig_profile_picture_url: Mapped[Optional[str]] = mapped_column(Text)
    ig_account_type: Mapped[Optional[str]] = mapped_column(String(50))  # business, creator, personal

    # Linked Facebook Page (required for messaging API)
    page_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    page_name: Mapped[Optional[str]] = mapped_column(String(255))

    # Tokens — always encrypted, never returned to frontend
    access_token_encrypted: Mapped[Optional[str]] = mapped_column(Text)
    page_access_token_encrypted: Mapped[Optional[str]] = mapped_column(Text)
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Meta-granted permissions and dynamic capabilities
    permissions: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    capabilities: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    # Webhook
    webhook_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    webhook_subscribed_fields: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    connected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_token_refresh: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="instagram_accounts")  # noqa
    automations: Mapped[list["Automation"]] = relationship(  # noqa
        "Automation", back_populates="ig_account", cascade="all, delete-orphan"
    )
    contacts: Mapped[list["Contact"]] = relationship(  # noqa
        "Contact", back_populates="ig_account", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<InstagramAccount @{self.ig_username}>"
