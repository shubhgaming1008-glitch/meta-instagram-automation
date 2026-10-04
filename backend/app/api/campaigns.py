"""Campaigns API router."""
from typing import Annotated, Optional
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import CurrentUser
from app.core.database import get_db
from app.models.campaign import Campaign

router = APIRouter()


class CampaignCreate(BaseModel):
    ig_account_id: str
    name: str
    description: Optional[str] = None


class CampaignResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    ig_account_id: str
    status: str
    total_triggers: int
    total_dms_sent: int
    total_link_clicks: int
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=list[CampaignResponse])
async def list_campaigns(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    ig_account_id: Optional[str] = None,
):
    query = select(Campaign).where(Campaign.user_id == current_user.id)
    if ig_account_id:
        query = query.where(Campaign.ig_account_id == ig_account_id)
    result = await db.execute(query.order_by(Campaign.created_at.desc()))
    return result.scalars().all()


@router.post("/", response_model=CampaignResponse, status_code=201)
async def create_campaign(
    body: CampaignCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    campaign = Campaign(
        user_id=current_user.id,
        ig_account_id=body.ig_account_id,
        name=body.name,
        description=body.description,
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.delete("/{campaign_id}", status_code=204)
async def delete_campaign(
    campaign_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
    )
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Campaign not found")
    await db.delete(c)
    await db.commit()
