"""
Automations CRUD router.
"""
from typing import Annotated, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import CurrentUser
from app.core.database import get_db
from app.models.automation import Automation, AutomationVersion
from app.models.workflow import WorkflowNode, WorkflowEdge
from datetime import datetime, timezone

router = APIRouter()


class TriggerConfig(BaseModel):
    match_mode: str = "any"
    keywords: list[str] = []
    case_insensitive: bool = True
    excluded_keywords: list[str] = []
    media_ids: list[str] = []
    keyword_groups: list[dict] = []


class AutomationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    ig_account_id: str
    campaign_id: Optional[str] = None
    trigger_type: str
    trigger_config: Optional[dict] = None


class AutomationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    trigger_config: Optional[dict] = None
    campaign_id: Optional[str] = None
    prevent_duplicate_dm: Optional[bool] = None
    duplicate_window_hours: Optional[int] = None


class FlowUpdate(BaseModel):
    nodes: list[dict]
    edges: list[dict]


class AutomationResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    ig_account_id: str
    campaign_id: Optional[str]
    trigger_type: str
    trigger_config: Optional[dict]
    status: str
    version: int
    total_runs: int
    total_dms_sent: int
    total_link_clicks: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=list[AutomationResponse])
async def list_automations(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    ig_account_id: Optional[str] = None,
):
    query = select(Automation).where(Automation.user_id == current_user.id)
    if ig_account_id:
        query = query.where(Automation.ig_account_id == ig_account_id)
    result = await db.execute(query.order_by(Automation.created_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=AutomationResponse, status_code=201)
async def create_automation(
    body: AutomationCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    automation = Automation(
        user_id=current_user.id,
        ig_account_id=body.ig_account_id,
        campaign_id=body.campaign_id,
        name=body.name,
        description=body.description,
        trigger_type=body.trigger_type,
        trigger_config=body.trigger_config or {},
        status="draft",
    )
    db.add(automation)
    await db.commit()
    await db.refresh(automation)
    return automation


@router.get("/{automation_id}", response_model=AutomationResponse)
async def get_automation(
    automation_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Automation).where(
            Automation.id == automation_id,
            Automation.user_id == current_user.id,
        )
    )
    auto = result.scalar_one_or_none()
    if not auto:
        raise HTTPException(status_code=404, detail="Automation not found")
    return auto


@router.patch("/{automation_id}", response_model=AutomationResponse)
async def update_automation(
    automation_id: str,
    body: AutomationUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Automation).where(
            Automation.id == automation_id,
            Automation.user_id == current_user.id,
        )
    )
    auto = result.scalar_one_or_none()
    if not auto:
        raise HTTPException(status_code=404, detail="Automation not found")

    update_data = body.model_dump(exclude_none=True)
    for k, v in update_data.items():
        setattr(auto, k, v)

    if body.status == "active" and not auto.published_at:
        auto.published_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(auto)
    return auto


@router.put("/{automation_id}/flow")
async def save_flow(
    automation_id: str,
    body: FlowUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Save the visual flow (nodes + edges) for an automation."""
    result = await db.execute(
        select(Automation).where(
            Automation.id == automation_id,
            Automation.user_id == current_user.id,
        )
    )
    auto = result.scalar_one_or_none()
    if not auto:
        raise HTTPException(status_code=404, detail="Automation not found")

    # Delete old nodes and edges
    from sqlalchemy import delete
    await db.execute(delete(WorkflowNode).where(WorkflowNode.automation_id == automation_id))
    await db.execute(delete(WorkflowEdge).where(WorkflowEdge.automation_id == automation_id))

    # Save new nodes
    for node_data in body.nodes:
        node = WorkflowNode(
            automation_id=automation_id,
            node_id_in_flow=node_data["id"],
            node_type=node_data.get("type", "unknown"),
            label=node_data.get("data", {}).get("label"),
            position_x=node_data.get("position", {}).get("x", 0),
            position_y=node_data.get("position", {}).get("y", 0),
            config=node_data.get("data", {}),
        )
        db.add(node)

    # Save new edges
    for edge_data in body.edges:
        edge = WorkflowEdge(
            automation_id=automation_id,
            edge_id_in_flow=edge_data["id"],
            source_node_id=edge_data["source"],
            target_node_id=edge_data["target"],
            source_handle=edge_data.get("sourceHandle"),
            condition_label=edge_data.get("label"),
        )
        db.add(edge)

    # Save version snapshot
    auto.version += 1
    auto.current_flow = {"nodes": body.nodes, "edges": body.edges}
    version = AutomationVersion(
        automation_id=automation_id,
        version=auto.version,
        snapshot={"nodes": body.nodes, "edges": body.edges},
        created_at=datetime.now(timezone.utc),
        created_by=current_user.id,
    )
    db.add(version)

    await db.commit()
    return {"status": "saved", "version": auto.version}


@router.get("/{automation_id}/flow")
async def get_flow(
    automation_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get the current flow (nodes + edges) for an automation."""
    result = await db.execute(
        select(Automation).where(
            Automation.id == automation_id,
            Automation.user_id == current_user.id,
        )
    )
    auto = result.scalar_one_or_none()
    if not auto:
        raise HTTPException(status_code=404, detail="Automation not found")

    nodes_result = await db.execute(
        select(WorkflowNode).where(WorkflowNode.automation_id == automation_id)
    )
    edges_result = await db.execute(
        select(WorkflowEdge).where(WorkflowEdge.automation_id == automation_id)
    )

    nodes = [
        {
            "id": n.node_id_in_flow,
            "type": n.node_type,
            "position": {"x": n.position_x, "y": n.position_y},
            "data": {**(n.config or {}), "label": n.label},
        }
        for n in nodes_result.scalars().all()
    ]
    edges = [
        {
            "id": e.edge_id_in_flow,
            "source": e.source_node_id,
            "target": e.target_node_id,
            "sourceHandle": e.source_handle,
            "label": e.condition_label,
        }
        for e in edges_result.scalars().all()
    ]

    return {"nodes": nodes, "edges": edges, "version": auto.version}


@router.post("/{automation_id}/publish")
async def publish_automation(
    automation_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Automation).where(
            Automation.id == automation_id,
            Automation.user_id == current_user.id,
        )
    )
    auto = result.scalar_one_or_none()
    if not auto:
        raise HTTPException(status_code=404, detail="Automation not found")
    auto.status = "active"
    auto.published_at = datetime.now(timezone.utc)
    await db.commit()
    return {"status": "active"}


@router.post("/{automation_id}/pause")
async def pause_automation(
    automation_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Automation).where(
            Automation.id == automation_id,
            Automation.user_id == current_user.id,
        )
    )
    auto = result.scalar_one_or_none()
    if not auto:
        raise HTTPException(status_code=404, detail="Automation not found")
    auto.status = "paused"
    await db.commit()
    return {"status": "paused"}


@router.delete("/{automation_id}", status_code=204)
async def delete_automation(
    automation_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Automation).where(
            Automation.id == automation_id,
            Automation.user_id == current_user.id,
        )
    )
    auto = result.scalar_one_or_none()
    if not auto:
        raise HTTPException(status_code=404, detail="Automation not found")
    await db.delete(auto)
    await db.commit()
