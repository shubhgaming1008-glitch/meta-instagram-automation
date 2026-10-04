"""Celery tasks for message sending."""
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


@celery_app.task(
    bind=True,
    name="app.tasks.message_tasks.send_follow_up",
    max_retries=3,
    queue="high_priority",
)
def send_follow_up(self, job_id: str):
    """Send a follow-up message for a paused job."""
    async def _send():
        from app.core.database import AsyncSessionLocal
        from app.services.automation_engine import AutomationEngine

        async with AsyncSessionLocal() as db:
            engine = AutomationEngine(db)
            await engine.execute_job(job_id)

    try:
        run_async(_send())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
