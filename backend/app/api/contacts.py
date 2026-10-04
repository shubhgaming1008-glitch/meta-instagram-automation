"""Contacts API router."""
from typing import Annotated, Optional
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import CurrentUser
from app.core.database import get_db
from app.models.contact import Contact
from app.models.log import ExecutionLog

router = APIRouter()


class ContactResponse(BaseModel):
    id: str
    ig_user_id: str
    username: Optional[str]
    display_name: Optional[str]
    email: Optional[str]
    first_interaction_at: Optional[datetime]
    last_interaction_at: Optional[datetime]
    status: str
    is_blocked: bool
    opted_out: bool
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=list[ContactResponse])
async def list_contacts(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    ig_account_id: Optional[str] = None,
    search: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    query = select(Contact)
    if ig_account_id:
        query = query.where(Contact.ig_account_id == ig_account_id)
    if search:
        query = query.where(
            Contact.username.ilike(f"%{search}%")
            | Contact.display_name.ilike(f"%{search}%")
            | Contact.email.ilike(f"%{search}%")
        )
    result = await db.execute(
        query.order_by(Contact.last_interaction_at.desc()).limit(limit).offset(offset)
    )
    return result.scalars().all()


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(404, "Contact not found")
    return contact


@router.get("/{contact_id}/timeline")
async def get_contact_timeline(
    contact_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get the full interaction timeline for a contact."""
    result = await db.execute(
        select(ExecutionLog)
        .where(ExecutionLog.contact_id == contact_id)
        .order_by(ExecutionLog.created_at.asc())
        .limit(200)
    )
    logs = result.scalars().all()
    return [
        {
            "id": log.id,
            "level": log.level,
            "category": log.category,
            "message": log.message,
            "node_type": log.node_type,
            "created_at": log.created_at,
        }
        for log in logs
    ]


@router.patch("/{contact_id}/opt-out")
async def opt_out_contact(
    contact_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Contact).where(Contact.id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(404, "Contact not found")
    contact.opted_out = True
    await db.commit()
    return {"status": "opted_out"}
