"""
Celery tasks for automation execution and webhook event processing.
"""
import asyncio
import hashlib
from datetime import datetime, timezone
from typing import Optional

import structlog
from celery import shared_task
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.celery_app import celery_app

log = structlog.get_logger()


def run_async(coro):
    """Run an async coroutine from a Celery task."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    bind=True,
    name="app.tasks.automation_tasks.process_webhook_event",
    max_retries=5,
    default_retry_delay=60,
    acks_late=True,
)
def process_webhook_event(self, webhook_event_id: str, object_type: str, field: str):
    """
    Process a raw webhook event — find matching automations and create jobs.
    """
    async def _process():
        from app.core.database import AsyncSessionLocal
        from app.models.event import WebhookEvent
        from app.services.event_processor import EventProcessor
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(WebhookEvent).where(WebhookEvent.id == webhook_event_id)
            )
            event = result.scalar_one_or_none()
            if not event:
                log.error("WebhookEvent not found", id=webhook_event_id)
                return

            processor = EventProcessor(db)
            await processor.process(event, object_type, field)

    try:
        run_async(_process())
    except Exception as exc:
        log.exception("process_webhook_event failed", event_id=webhook_event_id)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(
    bind=True,
    name="app.tasks.automation_tasks.execute_job",
    max_retries=5,
    acks_late=True,
)
def execute_job(self, job_id: str):
    """Execute an automation job."""
    async def _execute():
        from app.core.database import AsyncSessionLocal
        from app.services.automation_engine import AutomationEngine

        async with AsyncSessionLocal() as db:
            engine = AutomationEngine(db)
            await engine.execute_job(job_id)

    try:
        run_async(_execute())
    except Exception as exc:
        log.exception("execute_job failed", job_id=job_id)
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))


@celery_app.task(
    name="app.tasks.automation_tasks.trigger_automation",
    acks_late=True,
)
def trigger_automation(automation_id: str, contact_id: str, trigger_context: dict):
    """Manually trigger an automation for a contact."""
    async def _trigger():
        from app.core.database import AsyncSessionLocal
        from app.core.redis_client import acquire_lock
        from app.models.automation import Automation
        from app.models.job import Job
        from sqlalchemy import select

        idempotency_key = hashlib.sha256(
            f"{automation_id}:{contact_id}:{trigger_context.get('trigger_event_id', '')}".encode()
        ).hexdigest()

        async with AsyncSessionLocal() as db:
            # Check for duplicate job
            existing = await db.execute(
                select(Job).where(Job.idempotency_key == idempotency_key)
            )
            if existing.scalar_one_or_none():
                log.info("Duplicate job skipped", idempotency_key=idempotency_key)
                return

            # Check duplicate DM window
            result = await db.execute(
                select(Automation).where(Automation.id == automation_id)
            )
            automation = result.scalar_one_or_none()
            if not automation or automation.status != "active":
                return

            job = Job(
                automation_id=automation_id,
                contact_id=contact_id,
                status="pending",
                execution_context=trigger_context,
                idempotency_key=idempotency_key,
                created_at=datetime.now(timezone.utc),
                max_retries=5,
            )
            db.add(job)
            await db.flush()
            job_id = job.id
            await db.commit()

        # Dispatch execution task
        execute_job.delay(job_id)
        log.info("Job created and dispatched", job_id=job_id, automation_id=automation_id)

    run_async(_trigger())
