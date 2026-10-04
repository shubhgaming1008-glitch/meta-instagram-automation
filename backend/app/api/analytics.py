"""Analytics API router."""
from typing import Annotated, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import CurrentUser
from app.core.database import get_db
from app.models.automation import Automation
from app.models.contact import Contact
from app.models.link import Link, LinkClick
from app.models.message import Message
from app.models.job import Job

router = APIRouter()


@router.get("/overview")
async def get_overview(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    ig_account_id: Optional[str] = None,
    days: int = Query(30, ge=1, le=365),
):
    """Dashboard overview analytics."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Total automations
    auto_q = select(func.count(Automation.id)).where(Automation.user_id == current_user.id)
    total_automations = (await db.execute(auto_q)).scalar() or 0

    # Active automations
    active_q = select(func.count(Automation.id)).where(
        Automation.user_id == current_user.id,
        Automation.status == "active",
    )
    active_automations = (await db.execute(active_q)).scalar() or 0

    # Total jobs (automation runs)
    job_q = select(func.count(Job.id)).where(Job.created_at >= since)
    total_runs = (await db.execute(job_q)).scalar() or 0

    # DMs sent
    dm_q = select(func.count(Message.id)).where(
        Message.direction == "out",
        Message.is_automated == True,
        Message.sent_at >= since,
    )
    dms_sent = (await db.execute(dm_q)).scalar() or 0

    # Link clicks
    click_q = select(func.count(LinkClick.id)).where(LinkClick.clicked_at >= since)
    link_clicks = (await db.execute(click_q)).scalar() or 0

    # Total contacts
    contact_q = select(func.count(Contact.id))
    if ig_account_id:
        contact_q = contact_q.where(Contact.ig_account_id == ig_account_id)
    total_contacts = (await db.execute(contact_q)).scalar() or 0

    # Failed jobs
    failed_q = select(func.count(Job.id)).where(
        Job.status == "failed",
        Job.created_at >= since,
    )
    failed_jobs = (await db.execute(failed_q)).scalar() or 0

    return {
        "period_days": days,
        "total_automations": total_automations,
        "active_automations": active_automations,
        "total_runs": total_runs,
        "dms_sent": dms_sent,
        "link_clicks": link_clicks,
        "total_contacts": total_contacts,
        "failed_jobs": failed_jobs,
        "error_rate": round(failed_jobs / max(total_runs, 1) * 100, 2),
    }


@router.get("/automations/{automation_id}")
async def get_automation_analytics(
    automation_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    days: int = Query(30, ge=1, le=365),
):
    """Per-automation conversion funnel analytics."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    auto_q = select(Automation).where(
        Automation.id == automation_id,
        Automation.user_id == current_user.id,
    )
    result = await db.execute(auto_q)
    auto = result.scalar_one_or_none()
    if not auto:
        return {"error": "Automation not found"}

    runs_q = select(func.count(Job.id)).where(
        Job.automation_id == automation_id,
        Job.created_at >= since,
    )
    total_runs = (await db.execute(runs_q)).scalar() or 0

    completed_q = select(func.count(Job.id)).where(
        Job.automation_id == automation_id,
        Job.status == "completed",
        Job.created_at >= since,
    )
    completed = (await db.execute(completed_q)).scalar() or 0

    dms_q = select(func.count(Message.id)).where(
        Message.automation_id == automation_id,
        Message.direction == "out",
        Message.sent_at >= since,
    )
    dms_sent = (await db.execute(dms_q)).scalar() or 0

    clicks_q = select(func.count(LinkClick.id)).where(
        LinkClick.automation_id == automation_id,
        LinkClick.clicked_at >= since,
    )
    clicks = (await db.execute(clicks_q)).scalar() or 0

    return {
        "automation_id": automation_id,
        "automation_name": auto.name,
        "period_days": days,
        "total_runs": total_runs,
        "completed_runs": completed,
        "dms_sent": dms_sent,
        "link_clicks": clicks,
        "completion_rate": round(completed / max(total_runs, 1) * 100, 2),
    }
