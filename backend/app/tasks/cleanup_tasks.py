"""Celery periodic cleanup tasks."""
from datetime import datetime, timedelta, timezone

from app.core.celery_app import celery_app
import asyncio
import structlog

log = structlog.get_logger()


def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.tasks.cleanup_tasks.cleanup_expired_links", queue="low_priority")
def cleanup_expired_links():
    """Mark expired links as inactive."""
    async def _cleanup():
        from app.core.database import AsyncSessionLocal
        from app.models.link import Link
        from sqlalchemy import select, update

        async with AsyncSessionLocal() as db:
            now = datetime.now(timezone.utc)
            result = await db.execute(
                select(Link).where(
                    Link.expires_at < now,
                    Link.status == "active",
                )
            )
            links = result.scalars().all()
            for link in links:
                link.status = "expired"
                link.is_active = False
            await db.commit()
            log.info("Cleaned up expired links", count=len(links))

    run_async(_cleanup())


@celery_app.task(name="app.tasks.cleanup_tasks.cleanup_old_webhook_events", queue="low_priority")
def cleanup_old_webhook_events():
    """Remove webhook events older than 30 days."""
    async def _cleanup():
        from app.core.database import AsyncSessionLocal
        from app.models.event import WebhookEvent
        from sqlalchemy import delete

        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                delete(WebhookEvent).where(WebhookEvent.received_at < cutoff)
            )
            await db.commit()
            log.info("Cleaned up old webhook events", count=result.rowcount)

    run_async(_cleanup())
