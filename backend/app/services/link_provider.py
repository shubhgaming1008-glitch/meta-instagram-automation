"""
LinkProvider — handles protected link generation, tracking, and delivery.
"""
import hashlib
import ipaddress
from datetime import datetime, timezone
from typing import Optional

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import generate_secure_token
from app.models.link import Link, LinkClick

log = structlog.get_logger()


class LinkProvider:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_link(
        self,
        ig_account_id: str,
        name: str,
        destination_url: str,
        is_protected: bool = False,
        requires_follow: bool = False,
        campaign_id: Optional[str] = None,
        automation_id: Optional[str] = None,
        utm_params: Optional[dict] = None,
        expires_at: Optional[datetime] = None,
        max_clicks: Optional[int] = None,
        is_one_time: bool = False,
    ) -> Link:
        """Create a new tracked link."""
        self._validate_url(destination_url)
        token = generate_secure_token(24)

        link = Link(
            ig_account_id=ig_account_id,
            campaign_id=campaign_id,
            automation_id=automation_id,
            name=name,
            destination_url=destination_url,
            is_protected=is_protected,
            token=token,
            requires_follow=requires_follow,
            utm_params=utm_params or {},
            expires_at=expires_at,
            max_clicks=max_clicks,
            is_one_time_per_user=is_one_time,
            status="active",
        )
        self.db.add(link)
        await self.db.flush()
        return link

    def get_unlock_url(self, link: Link) -> str:
        """Generate the /unlock/{token} URL (never exposes destination)."""
        return f"{settings.effective_link_domain}/unlock/{link.token}"

    async def resolve_link(self, token: str, contact_id: Optional[str] = None, ip: Optional[str] = None) -> dict:
        """
        Resolve a token to its destination URL.
        Validates expiry, click limits, and records the click.
        Returns: {destination_url, link_id} or {error}
        """
        result = await self.db.execute(select(Link).where(Link.token == token))
        link = result.scalar_one_or_none()

        if not link:
            return {"error": "Link not found"}

        if not link.is_active or link.status != "active":
            return {"error": "Link is not active"}

        now = datetime.now(timezone.utc)
        if link.expires_at and link.expires_at < now:
            return {"error": "Link has expired"}

        if link.max_clicks and link.total_clicks >= link.max_clicks:
            return {"error": "Link click limit reached"}

        # Check one-time per user
        if link.is_one_time_per_user and contact_id:
            existing_click = await self.db.execute(
                select(LinkClick).where(
                    LinkClick.link_id == link.id,
                    LinkClick.contact_id == contact_id,
                )
            )
            if existing_click.scalar_one_or_none():
                return {"error": "Link already used by this user"}

        # Check if unique click (new user)
        is_unique = contact_id is not None
        if contact_id:
            prev = await self.db.execute(
                select(LinkClick).where(
                    LinkClick.link_id == link.id,
                    LinkClick.contact_id == contact_id,
                )
            )
            is_unique = prev.scalar_one_or_none() is None

        # Record click
        click = LinkClick(
            link_id=link.id,
            contact_id=contact_id,
            campaign_id=link.campaign_id,
            automation_id=link.automation_id,
            ip_hash=self._hash_ip(ip) if ip else None,
            clicked_at=now,
            is_unique=is_unique,
        )
        self.db.add(click)

        # Update counters
        link.total_clicks += 1
        if is_unique:
            link.unique_clicks += 1
        link.last_click_at = now

        await self.db.flush()

        # Build final URL with UTM params
        destination = self._append_utm(link.destination_url, link.utm_params or {})
        return {"destination_url": destination, "link_id": link.id, "link": link}

    async def deliver_link(
        self,
        link_id: Optional[str],
        contact_id: Optional[str],
        automation_id: Optional[str],
        campaign_id: Optional[str],
        context: dict,
    ) -> dict:
        """Send a link to a contact via DM."""
        if not link_id:
            return {"status": "error", "error": "No link_id configured on link node"}

        result = await self.db.execute(select(Link).where(Link.id == link_id))
        link = result.scalar_one_or_none()
        if not link:
            return {"status": "error", "error": "Link not found"}

        url = self.get_unlock_url(link) if link.is_protected else link.destination_url
        context["last_link_url"] = url
        context["last_link_id"] = link_id
        return {"status": "completed", "handle": "default", "url": url}

    def _validate_url(self, url: str):
        """Basic SSRF protection — reject private/internal URLs."""
        import re
        if not url.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        # Block common internal ranges
        blocked_patterns = [
            r"localhost",
            r"127\.",
            r"10\.",
            r"192\.168\.",
            r"172\.(1[6-9]|2\d|3[01])\.",
            r"169\.254\.",
            r"::1",
            r"metadata\.google",
        ]
        for pattern in blocked_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                raise ValueError(f"URL points to a restricted address: {url}")

    def _hash_ip(self, ip: str) -> str:
        """Hash IP address for privacy-safe storage."""
        return hashlib.sha256(ip.encode()).hexdigest()

    def _append_utm(self, url: str, utm_params: dict) -> str:
        if not utm_params:
            return url
        from urllib.parse import urlencode, urlparse, urlunparse, parse_qs
        parsed = urlparse(url)
        params = urlencode(utm_params)
        separator = "&" if parsed.query else "?"
        return f"{url}{separator}{params}"
