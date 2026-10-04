"""
EventProcessor — maps raw webhook events to automation triggers.
"""
import hashlib
from datetime import datetime, timezone
from typing import Optional

import structlog
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.automation import Automation
from app.models.contact import Contact
from app.models.event import WebhookEvent
from app.models.instagram_account import InstagramAccount
from app.services.keyword_engine import match_trigger_config

log = structlog.get_logger()


class EventProcessor:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process(self, event: WebhookEvent, object_type: str, field: str):
        """Route a webhook event to matching automations."""
        payload = event.raw_payload

        if object_type == "instagram" and field == "comments":
            await self._handle_comment(event, payload)
        elif object_type == "instagram" and field == "messaging":
            await self._handle_dm(event, payload)
        elif object_type == "instagram" and field == "story_insights":
            await self._handle_story(event, payload)
        elif object_type == "instagram" and field == "live_comments":
            await self._handle_live_comment(event, payload)
        else:
            log.info("Unhandled webhook event type", object_type=object_type, field=field)

        event.processed = True
        event.processed_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def _handle_comment(self, event: WebhookEvent, payload: dict):
        """Handle Instagram comment events."""
        comment_id = payload.get("id") or payload.get("comment_id")
        comment_text = payload.get("text", "")
        commenter_id = payload.get("from", {}).get("id")
        media_id = payload.get("media", {}).get("id") or payload.get("media_id")
        ig_account_id = await self._find_account_for_entry(payload)

        if not commenter_id or not ig_account_id:
            log.warning("Comment event missing commenter or account", payload=payload)
            return

        # Skip if commenter is the account owner (don't DM yourself)
        account = await self._get_account_by_id(ig_account_id)
        if account and commenter_id == account.ig_user_id:
            return

        # Find or create contact
        contact = await self._get_or_create_contact(ig_account_id, commenter_id)

        # Find matching active automations (comment trigger type)
        automations = await self._get_active_automations(ig_account_id, "comment")

        for automation in automations:
            trigger_config = automation.trigger_config or {}

            # Check media filter (specific post/reel vs all)
            media_filter = trigger_config.get("media_ids", [])
            if media_filter and media_id and media_id not in media_filter:
                continue

            # Match keyword/any-comment
            if not match_trigger_config(comment_text, trigger_config):
                continue

            # Build trigger context
            context = {
                "trigger_type": "comment",
                "trigger_comment_id": comment_id,
                "trigger_comment_text": comment_text,
                "trigger_media_id": media_id,
                "contact": {
                    "id": contact.id,
                    "ig_user_id": contact.ig_user_id,
                    "username": contact.username,
                    "email": contact.email,
                    "opted_out": contact.opted_out,
                },
                "contact_tags": [],
                "trigger_event_id": event.id,
            }

            from app.tasks.automation_tasks import trigger_automation
            trigger_automation.delay(
                automation_id=automation.id,
                contact_id=contact.id,
                trigger_context=context,
            )
            log.info("Comment triggered automation", automation_id=automation.id, contact=commenter_id)

    async def _handle_dm(self, event: WebhookEvent, payload: dict):
        """Handle incoming DM events (keyword triggers and button postbacks)."""
        sender_id = payload.get("sender", {}).get("id")
        recipient_id = payload.get("recipient", {}).get("id")
        message = payload.get("message", {})
        postback = payload.get("postback", {})
        ig_account_id = await self._find_account_by_ig_id(recipient_id)

        if not sender_id or not ig_account_id:
            return

        text = message.get("text", "") or postback.get("payload", "")
        contact = await self._get_or_create_contact(ig_account_id, sender_id)

        if contact.opted_out:
            return

        # Handle button postbacks
        if postback:
            await self._handle_postback(ig_account_id, contact, postback, event)
            return

        # DM keyword triggers
        automations = await self._get_active_automations(ig_account_id, "dm_keyword")
        for automation in automations:
            trigger_config = automation.trigger_config or {}
            if not match_trigger_config(text, trigger_config):
                continue

            context = {
                "trigger_type": "dm_keyword",
                "trigger_text": text,
                "contact": {
                    "id": contact.id,
                    "ig_user_id": contact.ig_user_id,
                    "username": contact.username,
                    "email": contact.email,
                    "opted_out": contact.opted_out,
                },
                "contact_tags": [],
                "trigger_event_id": event.id,
            }
            from app.tasks.automation_tasks import trigger_automation
            trigger_automation.delay(
                automation_id=automation.id,
                contact_id=contact.id,
                trigger_context=context,
            )

    async def _handle_postback(self, ig_account_id: str, contact: Contact, postback: dict, event: WebhookEvent):
        """Handle button click postbacks — resume paused jobs or trigger follow confirmation."""
        payload_value = postback.get("payload", "")
        log.info("Postback received", payload=payload_value, contact=contact.ig_user_id)

        # Follow confirmation postback
        if payload_value == "FOLLOW_CONFIRMED":
            from app.models.job import Job
            from sqlalchemy import update
            # Find the latest paused job for this contact and resume
            result = await self.db.execute(
                select(Job)
                .where(
                    and_(
                        Job.contact_id == contact.id,
                        Job.automation_id.isnot(None),
                    )
                )
                .order_by(Job.created_at.desc())
                .limit(1)
            )
            job = result.scalar_one_or_none()
            if job and job.status == "pending":
                ctx = job.execution_context or {}
                ctx["follow_confirmed"] = True
                job.execution_context = ctx
                await self.db.flush()
                from app.tasks.automation_tasks import execute_job
                execute_job.delay(job.id)

    async def _handle_story(self, event: WebhookEvent, payload: dict):
        """Handle story reply/mention events."""
        sender_id = payload.get("sender", {}).get("id")
        recipient_id = payload.get("recipient", {}).get("id")
        ig_account_id = await self._find_account_by_ig_id(recipient_id)

        if not sender_id or not ig_account_id:
            return

        contact = await self._get_or_create_contact(ig_account_id, sender_id)
        message = payload.get("message", {})
        text = message.get("text", "")

        automations = await self._get_active_automations(ig_account_id, "story_reply")
        for automation in automations:
            if not match_trigger_config(text, automation.trigger_config or {}):
                continue
            context = {"trigger_type": "story_reply", "trigger_text": text, "trigger_event_id": event.id}
            from app.tasks.automation_tasks import trigger_automation
            trigger_automation.delay(automation.id, contact.id, context)

    async def _handle_live_comment(self, event: WebhookEvent, payload: dict):
        """Handle live comment events (eligibility-gated)."""
        log.info("Live comment event received — processing if eligible")
        # Similar to comment handler but for live streams

    async def _get_or_create_contact(self, ig_account_id: str, ig_user_id: str) -> Contact:
        """Find or create a contact record."""
        result = await self.db.execute(
            select(Contact).where(
                and_(
                    Contact.ig_account_id == ig_account_id,
                    Contact.ig_user_id == ig_user_id,
                )
            )
        )
        contact = result.scalar_one_or_none()
        if not contact:
            now = datetime.now(timezone.utc)
            contact = Contact(
                ig_account_id=ig_account_id,
                ig_user_id=ig_user_id,
                first_interaction_at=now,
                last_interaction_at=now,
            )
            self.db.add(contact)
            await self.db.flush()
        else:
            contact.last_interaction_at = datetime.now(timezone.utc)
            await self.db.flush()
        return contact

    async def _get_active_automations(self, ig_account_id: str, trigger_type: str) -> list[Automation]:
        result = await self.db.execute(
            select(Automation).where(
                and_(
                    Automation.ig_account_id == ig_account_id,
                    Automation.trigger_type == trigger_type,
                    Automation.status == "active",
                )
            )
        )
        return list(result.scalars().all())

    async def _find_account_for_entry(self, payload: dict) -> Optional[str]:
        """Find ig_account_id from webhook entry payload."""
        ig_id = (
            payload.get("recipient", {}).get("id")
            or payload.get("business_account_id")
        )
        if ig_id:
            return await self._find_account_by_ig_id(ig_id)
        return None

    async def _find_account_by_ig_id(self, ig_id: str) -> Optional[str]:
        if not ig_id:
            return None
        result = await self.db.execute(
            select(InstagramAccount).where(
                and_(
                    InstagramAccount.ig_user_id == ig_id,
                    InstagramAccount.is_active == True,
                )
            )
        )
        account = result.scalar_one_or_none()
        return account.id if account else None

    async def _get_account_by_id(self, account_id: str) -> Optional[InstagramAccount]:
        result = await self.db.execute(
            select(InstagramAccount).where(InstagramAccount.id == account_id)
        )
        return result.scalar_one_or_none()
