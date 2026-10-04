"""Inbox API router."""
from typing import Annotated, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import CurrentUser
from app.core.database import get_db
from app.models.message import Conversation, Message

router = APIRouter()


@router.get("/conversations")
async def list_conversations(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    ig_account_id: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    query = select(Conversation)
    if ig_account_id:
        query = query.where(Conversation.ig_account_id == ig_account_id)
    result = await db.execute(
        query.order_by(Conversation.last_message_at.desc()).limit(limit).offset(offset)
    )
    convs = result.scalars().all()
    return [
        {
            "id": c.id,
            "contact_id": c.contact_id,
            "ig_account_id": c.ig_account_id,
            "status": c.status,
            "unread_count": c.unread_count,
            "last_message_at": c.last_message_at,
            "last_message_preview": c.last_message_preview,
            "is_automated": c.is_automated,
        }
        for c in convs
    ]


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.sent_at.asc())
    )
    msgs = result.scalars().all()
    return [
        {
            "id": m.id,
            "direction": m.direction,
            "message_type": m.message_type,
            "content": m.content,
            "status": m.status,
            "sent_at": m.sent_at,
            "is_automated": m.is_automated,
        }
        for m in msgs
    ]
