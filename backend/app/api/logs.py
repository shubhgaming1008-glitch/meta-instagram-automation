"""Logs API router."""
from typing import Annotated, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import CurrentUser
from app.core.database import get_db
from app.models.log import ExecutionLog

router = APIRouter()


@router.get("/")
async def list_logs(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    automation_id: Optional[str] = None,
    contact_id: Optional[str] = None,
    level: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
):
    query = select(ExecutionLog)
    if automation_id:
        query = query.where(ExecutionLog.automation_id == automation_id)
    if contact_id:
        query = query.where(ExecutionLog.contact_id == contact_id)
    if level:
        query = query.where(ExecutionLog.level == level)
    if category:
        query = query.where(ExecutionLog.category == category)

    result = await db.execute(
        query.order_by(ExecutionLog.created_at.desc()).limit(limit).offset(offset)
    )
    logs = result.scalars().all()
    return [
        {
            "id": log.id,
            "level": log.level,
            "category": log.category,
            "message": log.message,
            "automation_id": log.automation_id,
            "contact_id": log.contact_id,
            "node_id": log.node_id,
            "node_type": log.node_type,
            "api_status_code": log.api_status_code,
            "retry_count": log.retry_count,
            "final_state": log.final_state,
            "created_at": log.created_at,
        }
        for log in logs
    ]
