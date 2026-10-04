"""
Celery application configuration.
"""
from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "igauto",
    broker=settings.effective_broker_url,
    backend=settings.effective_result_backend,
    include=[
        "app.tasks.automation_tasks",
        "app.tasks.message_tasks",
        "app.tasks.cleanup_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    # Queue routing
    task_routes={
        "app.tasks.automation_tasks.*": {"queue": "default"},
        "app.tasks.message_tasks.*": {"queue": "high_priority"},
        "app.tasks.cleanup_tasks.*": {"queue": "low_priority"},
    },
    # Retry defaults
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=5,
    # Beat schedule (for periodic tasks)
    beat_schedule={
        "cleanup-expired-links": {
            "task": "app.tasks.cleanup_tasks.cleanup_expired_links",
            "schedule": 3600.0,  # every hour
        },
        "cleanup-old-webhook-events": {
            "task": "app.tasks.cleanup_tasks.cleanup_old_webhook_events",
            "schedule": 86400.0,  # every day
        },
    },
)
