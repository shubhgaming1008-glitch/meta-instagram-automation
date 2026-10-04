"""
Webhook receiver for Meta/Instagram events.
Includes HMAC-SHA256 signature verification and event deduplication.
"""
import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any

import structlog
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from typing import Annotated

from app.core.config import settings
from app.core.database import get_db
from app.core.redis_client import is_event_processed, mark_event_processed
from app.models.event import WebhookEvent

log = structlog.get_logger()
router = APIRouter()


def verify_meta_signature(payload: bytes, signature_header: str) -> bool:
    """Verify Meta webhook HMAC-SHA256 signature."""
    if not settings.META_APP_SECRET:
        log.warning("META_APP_SECRET not configured — skipping signature verification")
        return True  # Skip in unconfigured state (dev only)
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(
        settings.META_APP_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    received = signature_header[7:]  # strip "sha256="
    return hmac.compare_digest(expected, received)


from fastapi import Query
from fastapi.responses import PlainTextResponse

@router.get("/meta")
async def webhook_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """Meta webhook verification challenge (GET request)."""
    if hub_mode != "subscribe":
        raise HTTPException(status_code=400, detail="Invalid hub.mode")
    if hub_verify_token != settings.META_WEBHOOK_VERIFY_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid verify token")
    log.info("Meta webhook verified")
    return PlainTextResponse(content=str(hub_challenge))


@router.post("/meta")
async def webhook_receive(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256"),
):
    """Receive and queue Meta webhook events."""
    raw_body = await request.body()

    # 1. Verify signature
    if not verify_meta_signature(raw_body, x_hub_signature_256):
        log.warning("Webhook signature verification failed")
        raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # 2. Log raw event and deduplicate
    background_tasks.add_task(_process_webhook_payload, payload, db)

    # Return 200 immediately (Meta requires fast response)
    return {"status": "received"}


async def _process_webhook_payload(payload: dict, db: AsyncSession):
    """Background task: deduplicate and queue each event entry."""
    object_type = payload.get("object", "")
    entries = payload.get("entry", [])

    for entry in entries:
        entry_id = entry.get("id", "")
        # Each entry can have multiple messaging/comment events
        for field, events in _extract_field_events(entry):
            for event in events:
                event_id = _build_event_id(object_type, entry_id, field, event)
                if await is_event_processed(event_id):
                    log.info("Duplicate webhook event skipped", event_id=event_id)
                    continue

                # Store raw event
                webhook_event = WebhookEvent(
                    event_type=f"{object_type}.{field}",
                    ig_event_id=event_id,
                    raw_payload=event,
                    received_at=datetime.now(timezone.utc),
                    processed=False,
                )
                db.add(webhook_event)
                await db.flush()

                # Mark as processed in Redis (fast dedup)
                await mark_event_processed(event_id)

                # Dispatch to Celery
                from app.tasks.automation_tasks import process_webhook_event
                process_webhook_event.delay(str(webhook_event.id), object_type, field)

                log.info("Webhook event queued", event_id=event_id, type=f"{object_type}.{field}")

    await db.commit()


def _extract_field_events(entry: dict):
    """Yield (field_name, [events]) from a webhook entry."""
    for field in ["messaging", "comments", "story_insights", "feed", "live_comments"]:
        items = entry.get(field, [])
        if items:
            yield field, items if isinstance(items, list) else [items]


def _build_event_id(object_type: str, entry_id: str, field: str, event: dict) -> str:
    """Build a unique, deterministic event ID for deduplication."""
    # Use Meta's mid/comment_id where available, else hash the payload
    mid = event.get("message", {}).get("mid") or event.get("id") or ""
    if mid:
        return f"{object_type}:{entry_id}:{field}:{mid}"
    # Fallback: content hash
    content_hash = hashlib.sha256(json.dumps(event, sort_keys=True).encode()).hexdigest()[:16]
    return f"{object_type}:{entry_id}:{field}:{content_hash}"
