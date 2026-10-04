"""Tags API router."""
from typing import Annotated, Optional
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import CurrentUser
from app.core.database import get_db
from app.models.tag import Tag

router = APIRouter()


class TagCreate(BaseModel):
    ig_account_id: str
    name: str
    color: str = "#6366f1"
    description: Optional[str] = None


class TagResponse(BaseModel):
    id: str
    name: str
    color: str
    description: Optional[str]
    ig_account_id: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=list[TagResponse])
async def list_tags(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    ig_account_id: Optional[str] = None,
):
    query = select(Tag)
    if ig_account_id:
        query = query.where(Tag.ig_account_id == ig_account_id)
    result = await db.execute(query.order_by(Tag.name))
    return result.scalars().all()


@router.post("/", response_model=TagResponse, status_code=201)
async def create_tag(
    body: TagCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    tag = Tag(
        ig_account_id=body.ig_account_id,
        name=body.name,
        color=body.color,
        description=body.description,
    )
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


@router.delete("/{tag_id}", status_code=204)
async def delete_tag(
    tag_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(404, "Tag not found")
    await db.delete(tag)
    await db.commit()
