"""
Tag and ContactTag models.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Tag(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tags"

    ig_account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("instagram_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(20), default="#6366f1", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))

    # Contacts using this tag
    contact_tags: Mapped[list["ContactTag"]] = relationship(
        "ContactTag", back_populates="tag", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("ig_account_id", "name", name="uq_tag_account_name"),
    )

    def __repr__(self) -> str:
        return f"<Tag {self.name}>"


class ContactTag(Base):
    __tablename__ = "contact_tags"

    contact_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("contacts.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    added_by_automation_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("automations.id", ondelete="SET NULL"), nullable=True
    )

    contact: Mapped["Contact"] = relationship("Contact", back_populates="tags")  # noqa
    tag: Mapped["Tag"] = relationship("Tag", back_populates="contact_tags")
