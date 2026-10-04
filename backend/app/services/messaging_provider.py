"""
MessagingProvider — wraps Meta Messaging API for DM sending and comment replies.
All actual Meta API calls happen here. Never call Meta API directly from routers.
"""
import random
from datetime import datetime, timezone
from typing import Optional

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import decrypt_token
from app.models.contact import Contact
from app.models.instagram_account import InstagramAccount
from app.models.message import Message

log = structlog.get_logger()


class MessagingProvider:
    """
    Handles all DM and comment reply interactions with the Meta Graph API.
    Supports: text messages, buttons, quick replies, images.
    """

    async def send_message(
        self,
        ig_account_id: str,
        contact_id: Optional[str],
        message_config: dict,
        context: dict,
    ) -> dict:
        """
        Send a DM to a contact.

        message_config structure:
        {
            "type": "text" | "buttons" | "quick_reply" | "image",
            "text": "Hey! ...",
            "variants": ["msg1", "msg2"],  // random selection
            "buttons": [
                {"title": "GET LINK", "type": "postback", "payload": "GET_LINK"}
            ],
            "quick_replies": [
                {"title": "Yes", "payload": "YES"}
            ]
        }
        """
        async with AsyncSessionLocal() as db:
            account = await self._get_account(db, ig_account_id)
            if not account:
                return {"status": "error", "error": "Instagram account not found"}

            contact = await self._get_contact(db, contact_id)
            if not contact:
                return {"status": "error", "error": "Contact not found"}

            ig_recipient_id = contact.ig_user_id
            access_token = decrypt_token(account.page_access_token_encrypted or account.access_token_encrypted)

            # Build message payload
            message_payload = self._build_message_payload(message_config, context)

            # Call Meta API
            result = await self._call_send_api(
                page_id=account.page_id or account.ig_user_id,
                recipient_id=ig_recipient_id,
                message=message_payload,
                access_token=access_token,
            )

            if result.get("error"):
                log.error("DM send failed", error=result["error"], contact=contact.ig_user_id)
                await self._save_message(db, account, contact, message_config, "failed", result.get("error"))
                return {"status": "error", "error": str(result["error"])}

            await self._save_message(
                db, account, contact, message_payload,
                "sent", None,
                ig_message_id=result.get("message_id"),
            )
            await db.commit()

            log.info("DM sent", contact=contact.ig_user_id, msg_id=result.get("message_id"))
            return {"status": "completed", "handle": "default", "message_id": result.get("message_id")}

    async def reply_to_comment(
        self,
        ig_account_id: str,
        comment_id: str,
        message_config: dict,
        context: dict,
    ) -> dict:
        """Reply publicly to an Instagram comment."""
        async with AsyncSessionLocal() as db:
            account = await self._get_account(db, ig_account_id)
            if not account:
                return {"status": "error", "error": "Account not found"}

            access_token = decrypt_token(account.page_access_token_encrypted or account.access_token_encrypted)

            # Select text variant if multiple
            text = self._resolve_text(message_config, context)

            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{settings.meta_base_url}/{comment_id}/replies",
                    json={"message": text, "access_token": access_token},
                    timeout=10.0,
                )
                data = resp.json()

            if "error" in data:
                log.error("Comment reply failed", error=data["error"])
                return {"status": "error", "error": str(data["error"])}

            log.info("Comment reply sent", comment_id=comment_id)
            return {"status": "completed", "handle": "default"}

    def _build_message_payload(self, config: dict, context: dict) -> dict:
        """Build the Meta API message payload from node config."""
        msg_type = config.get("type", "text")
        text = self._resolve_text(config, context)

        if msg_type == "text":
            return {"text": text}

        if msg_type == "buttons":
            buttons = [
                {
                    "type": btn.get("type", "postback"),
                    "title": btn.get("title", ""),
                    "payload": btn.get("payload", btn.get("title", "").upper()),
                }
                for btn in config.get("buttons", [])[:3]  # Meta limit: 3 buttons
            ]
            return {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "button",
                        "text": text,
                        "buttons": buttons,
                    },
                }
            }

        if msg_type == "quick_reply":
            qrs = [
                {
                    "content_type": "text",
                    "title": qr.get("title", ""),
                    "payload": qr.get("payload", qr.get("title", "").upper()),
                }
                for qr in config.get("quick_replies", [])[:11]  # Meta limit: 11
            ]
            return {"text": text, "quick_replies": qrs}

        return {"text": text}

    def _resolve_text(self, config: dict, context: dict) -> str:
        """Pick a text variant randomly if multiple are provided."""
        variants = config.get("variants", [])
        if variants:
            text = random.choice(variants)
        else:
            text = config.get("text", "")

        # Simple template substitution
        username = context.get("contact", {}).get("username", "there")
        text = text.replace("{{username}}", username).replace("{{name}}", username)
        return text

    async def _call_send_api(
        self,
        page_id: str,
        recipient_id: str,
        message: dict,
        access_token: str,
    ) -> dict:
        """Make the actual Meta Graph API send request."""
        payload = {
            "recipient": {"id": recipient_id},
            "message": message,
            "access_token": access_token,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{settings.meta_base_url}/{page_id}/messages",
                json=payload,
            )
            return resp.json()

    async def _get_account(self, db: AsyncSession, account_id: str) -> Optional[InstagramAccount]:
        result = await db.execute(select(InstagramAccount).where(InstagramAccount.id == account_id))
        return result.scalar_one_or_none()

    async def _get_contact(self, db: AsyncSession, contact_id: str) -> Optional[Contact]:
        result = await db.execute(select(Contact).where(Contact.id == contact_id))
        return result.scalar_one_or_none()

    async def _save_message(
        self,
        db: AsyncSession,
        account: InstagramAccount,
        contact: Contact,
        content: dict,
        status: str,
        error: Optional[str],
        ig_message_id: Optional[str] = None,
    ):
        msg = Message(
            ig_account_id=account.id,
            contact_id=contact.id,
            direction="out",
            message_type=content.get("type", "text"),
            content=content,
            ig_message_id=ig_message_id,
            sent_at=datetime.now(timezone.utc) if status == "sent" else None,
            status=status,
            error=error,
            is_automated=True,
        )
        db.add(msg)
        await db.flush()
