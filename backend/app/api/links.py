"""Links API router."""
from typing import Annotated, Optional
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import CurrentUser
from app.core.database import get_db
from app.models.link import Link
from app.services.link_provider import LinkProvider

router = APIRouter()


class LinkCreate(BaseModel):
    ig_account_id: str
    name: str
    destination_url: str
    is_protected: bool = False
    requires_follow: bool = False
    campaign_id: Optional[str] = None
    automation_id: Optional[str] = None
    utm_params: Optional[dict] = None
    expires_at: Optional[datetime] = None
    max_clicks: Optional[int] = None
    is_one_time: bool = False


class LinkResponse(BaseModel):
    id: str
    name: str
    destination_url: str
    is_protected: bool
    token: str
    status: str
    total_clicks: int
    unique_clicks: int
    total_unlocks: int
    last_click_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/", response_model=LinkResponse, status_code=201)
async def create_link(
    body: LinkCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    provider = LinkProvider(db)
    link = await provider.create_link(
        ig_account_id=body.ig_account_id,
        name=body.name,
        destination_url=body.destination_url,
        is_protected=body.is_protected,
        requires_follow=body.requires_follow,
        campaign_id=body.campaign_id,
        automation_id=body.automation_id,
        utm_params=body.utm_params,
        expires_at=body.expires_at,
        max_clicks=body.max_clicks,
        is_one_time=body.is_one_time,
    )
    await db.commit()
    await db.refresh(link)
    return link


@router.get("/", response_model=list[LinkResponse])
async def list_links(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    ig_account_id: Optional[str] = None,
):
    query = select(Link)
    if ig_account_id:
        query = query.where(Link.ig_account_id == ig_account_id)
    result = await db.execute(query.order_by(Link.created_at.desc()))
    return result.scalars().all()


@router.delete("/{link_id}", status_code=204)
async def delete_link(
    link_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Link).where(Link.id == link_id))
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(404, "Link not found")
    await db.delete(link)
    await db.commit()


# ── Public unlock endpoint (no auth required) ─────────────────────
@router.get("/unlock/{token}")
async def unlock_link(
    token: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Resolve a protected link token to its destination.
    This is the public-facing endpoint accessed when a user clicks the link.
    """
    provider = LinkProvider(db)
    client_ip = request.client.host if request.client else None
    result = await provider.resolve_link(token=token, ip=client_ip)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    await db.commit()

    # Return the destination URL — frontend handles redirect
    return {
        "destination_url": result["destination_url"],
        "link_id": result["link_id"],
    }
