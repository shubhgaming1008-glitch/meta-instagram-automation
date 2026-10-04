"""
Workflow Node and Edge models for the visual flow builder.
"""
from typing import Optional

from sqlalchemy import Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class WorkflowNode(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Represents a single node in the visual flow builder.

    node_type options:
      trigger, message, comment_reply, button, quick_reply,
      condition, follow_check, link, delay, randomizer,
      tag, remove_tag, collect_email, collect_text,
      http_request, start_automation, end, ai_response
    """
    __tablename__ = "workflow_nodes"

    automation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("automations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # The React Flow node ID (client-assigned, unique within an automation)
    node_id_in_flow: Mapped[str] = mapped_column(String(100), nullable=False)
    node_type: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[Optional[str]] = mapped_column(String(255))

    # Visual position
    position_x: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    position_y: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Node-specific configuration (varies by type)
    config: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    automation: Mapped["Automation"] = relationship(  # noqa
        "Automation", back_populates="nodes"
    )

    def __repr__(self) -> str:
        return f"<WorkflowNode {self.node_type} [{self.node_id_in_flow}]>"


class WorkflowEdge(UUIDPrimaryKeyMixin, Base):
    """
    Represents a directed connection between two nodes.
    """
    __tablename__ = "workflow_edges"

    automation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("automations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # React Flow edge ID
    edge_id_in_flow: Mapped[str] = mapped_column(String(100), nullable=False)
    source_node_id: Mapped[str] = mapped_column(String(100), nullable=False)  # node_id_in_flow
    target_node_id: Mapped[str] = mapped_column(String(100), nullable=False)  # node_id_in_flow
    source_handle: Mapped[Optional[str]] = mapped_column(String(100))  # e.g., "yes", "no", "default"
    condition_label: Mapped[Optional[str]] = mapped_column(String(255))
    config: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    automation: Mapped["Automation"] = relationship(  # noqa
        "Automation", back_populates="edges"
    )
