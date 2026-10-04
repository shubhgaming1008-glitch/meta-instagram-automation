"""
Instagram / Meta OAuth integration router.
"""
from typing import Annotated
from urllib.parse import urlencode

import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.core.config import settings
from app.core.database import get_db
from app.core.security import encrypt_token, generate_secure_token
from app.models.instagram_account import InstagramAccount
from app.services.capability_service import CapabilityService

log = structlog.get_logger()
router = APIRouter()

# Required scopes
OAUTH_SCOPES = [
    "instagram_basic",
    "instagram_manage_comments",
    "instagram_manage_messages",
    "pages_show_list",
    "pages_read_engagement",
    "pages_messaging",
    "pages_manage_metadata",
    "pages_manage_posts",
]


class InstagramAccountResponse(BaseModel):
    id: str
    ig_user_id: str
    ig_username: str | None
    ig_name: str | None
    ig_account_type: str | None
    page_id: str | None
    page_name: str | None
    webhook_verified: bool
    is_active: bool
    capabilities: dict | None

    class Config:
        from_attributes = True


class CapabilityResponse(BaseModel):
    capabilities: dict
    permissions: list[str]


@router.get("/oauth/start")
async def oauth_start(current_user: CurrentUser):
    """Generate Meta OAuth URL and redirect."""
    if not settings.META_APP_ID:
        raise HTTPException(status_code=503, detail="Meta App ID not configured. Set META_APP_ID in .env")

    state = f"{current_user.id}::{generate_secure_token(16)}"
    params = {
        "client_id": settings.META_APP_ID,
        "redirect_uri": f"{settings.BASE_URL}/api/instagram/oauth/callback",
        "scope": ",".join(OAUTH_SCOPES),
        "response_type": "code",
        "state": state,
    }
    url = f"https://www.facebook.com/dialog/oauth?{urlencode(params)}"
    return {"oauth_url": url, "state": state}


@router.get("/debug/token")
async def debug_token(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Debug endpoint: show what pages and IG accounts are accessible with stored token."""
    from app.core.security import decrypt_token

    result = await db.execute(
        select(InstagramAccount).where(InstagramAccount.user_id == current_user.id)
    )
    account = result.scalars().first()
    if not account:
        return {"error": "No account found"}

    token_enc = account.page_access_token_encrypted or account.access_token_encrypted
    if not token_enc:
        return {"error": "No token stored"}

    token = decrypt_token(token_enc)

    async with httpx.AsyncClient() as client:
        me = await client.get(
            f"{settings.meta_base_url}/me",
            params={"fields": "id,name,accounts{id,name,instagram_business_account{id,username,name}}", "access_token": token}
        )
        me_data = me.json()

        # Also test direct ig_user_id
        direct_test = None
        if account.ig_user_id:
            r = await client.get(
                f"{settings.meta_base_url}/{account.ig_user_id}",
                params={"fields": "id,username,name", "access_token": token}
            )
            direct_test = r.json()

        return {
            "stored_ig_user_id": account.ig_user_id,
            "stored_page_id": account.page_id,
            "stored_ig_username": account.ig_username,
            "me_response": me_data,
            "direct_ig_test": direct_test,
        }


@router.get("/oauth/callback")
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Handle OAuth callback from Meta."""
    if not settings.META_APP_ID or not settings.META_APP_SECRET:
        raise HTTPException(status_code=503, detail="Meta app credentials not configured")

    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_resp = await client.get(
            f"{settings.meta_base_url}/oauth/access_token",
            params={
                "client_id": settings.META_APP_ID,
                "client_secret": settings.META_APP_SECRET,
                "redirect_uri": f"{settings.BASE_URL}/api/instagram/oauth/callback",
                "code": code,
            },
        )
        if token_resp.status_code != 200:
            log.error("Token exchange failed", response=token_resp.text)
            raise HTTPException(status_code=400, detail="OAuth token exchange failed")

        token_data = token_resp.json()
        short_lived_token = token_data.get("access_token")

        # Exchange for long-lived token
        ll_resp = await client.get(
            f"{settings.meta_base_url}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": settings.META_APP_ID,
                "client_secret": settings.META_APP_SECRET,
                "fb_exchange_token": short_lived_token,
            },
        )
        ll_data = ll_resp.json()
        long_lived_token = ll_data.get("access_token")

        # Fetch user info
        me_resp = await client.get(
            f"{settings.meta_base_url}/me",
            params={"fields": "id,name,accounts", "access_token": long_lived_token},
        )
        me_data = me_resp.json()

        user_fb_id = me_data.get("id")
        user_name = me_data.get("name")

        # Fetch connected Instagram Business Account
        ig_data = await _fetch_instagram_account(long_lived_token, me_data)

        # Save to DB (upsert)
        existing = await db.execute(
            select(InstagramAccount).where(InstagramAccount.ig_user_id == ig_data.get("id", user_fb_id))
        )
        account = existing.scalar_one_or_none()

        if not account:
            account = InstagramAccount(
                user_id=state.split("::")[0],  # Properly extract the user_id
                ig_user_id=ig_data.get("id", user_fb_id),
            )
            db.add(account)

        account.ig_username = ig_data.get("username")
        account.ig_name = ig_data.get("name") or user_name
        account.ig_account_type = ig_data.get("account_type", "").lower()
        account.access_token_encrypted = encrypt_token(long_lived_token)
        
        page_token = ig_data.get("page_token")
        if page_token and ig_data.get("page_id"):
            account.page_id = ig_data["page_id"]
            account.page_name = ig_data["page_name"]
            account.page_access_token_encrypted = encrypt_token(page_token)
            
            # Subscribe the page to webhooks!
            sub_resp = await client.post(
                f"{settings.meta_base_url}/{ig_data['page_id']}/subscribed_apps",
                params={
                    "subscribed_fields": "messages,messaging_postbacks,comments,message_reactions",
                    "access_token": page_token
                }
            )
            if sub_resp.status_code == 200:
                account.webhook_subscribed_fields = ["messages", "messaging_postbacks", "comments", "message_reactions"]
                account.webhook_verified = True

        account.is_active = True

        await db.flush()
        await db.commit()

        log.info("Instagram account connected", ig_user_id=account.ig_user_id)
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/settings/instagram?connected=true")


async def _fetch_instagram_account(token: str, me_data: dict) -> dict:
    """Fetch Instagram account details from connected Facebook Pages."""
    async with httpx.AsyncClient() as client:
        pages = me_data.get("accounts", {}).get("data", [])
        log.info("Fetching IG accounts from pages", page_count=len(pages))
        
        for page in pages:
            page_token = page.get("access_token")
            page_id = page["id"]
            
            # Try new API endpoint first: instagram_business_account
            ig_resp = await client.get(
                f"{settings.meta_base_url}/{page_id}",
                params={
                    "fields": "instagram_business_account{id,username,name,account_type}",
                    "access_token": page_token
                },
            )
            ig_resp_data = ig_resp.json()
            log.info("Page IG business account response", page_id=page_id, data=ig_resp_data)
            
            iba = ig_resp_data.get("instagram_business_account")
            if iba and iba.get("id"):
                return {
                    "id": iba["id"],
                    "username": iba.get("username"),
                    "name": iba.get("name"),
                    "account_type": iba.get("account_type", "business"),
                    "page_id": page_id,
                    "page_name": page["name"],
                    "page_token": page_token,
                }
            
            # Fallback: try old endpoint instagram_accounts
            ig_resp2 = await client.get(
                f"{settings.meta_base_url}/{page_id}/instagram_accounts",
                params={"fields": "id,username,name,account_type", "access_token": page_token},
            )
            ig_data2 = ig_resp2.json().get("data", [])
            log.info("Page instagram_accounts fallback", page_id=page_id, data=ig_data2)
            if ig_data2:
                return {**ig_data2[0], "page_id": page_id, "page_name": page["name"], "page_token": page_token}

        log.warning("No Instagram account found for any page", pages=[p["id"] for p in pages])
        return {}



@router.get("/accounts", response_model=list[InstagramAccountResponse])
async def list_accounts(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all connected Instagram accounts."""
    result = await db.execute(
        select(InstagramAccount).where(InstagramAccount.user_id == current_user.id)
    )
    return result.scalars().all()


@router.get("/accounts/{account_id}/posts")
async def list_posts(
    account_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 20,
):
    """Fetch recent posts/reels for a connected Instagram account."""
    from app.core.security import decrypt_token

    result = await db.execute(
        select(InstagramAccount).where(
            InstagramAccount.id == account_id,
            InstagramAccount.user_id == current_user.id,
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Use page access token if available, otherwise user token
    token_enc = account.page_access_token_encrypted or account.access_token_encrypted
    if not token_enc:
        raise HTTPException(status_code=400, detail="No access token available. Please reconnect Instagram.")

    token = decrypt_token(token_enc)

    async with httpx.AsyncClient() as client:
        ig_user_id = None
        ig_username = account.ig_username

        # Strategy 0: Try stored ig_user_id directly (it may already be the correct IG user ID)
        if account.ig_user_id:
            test_resp = await client.get(
                f"{settings.meta_base_url}/{account.ig_user_id}",
                params={"fields": "id,username", "access_token": token},
            )
            test_data = test_resp.json()
            if "error" not in test_data and test_data.get("id"):
                ig_user_id = test_data["id"]
                ig_username = test_data.get("username") or ig_username
                if not account.ig_username and ig_username:
                    account.ig_username = ig_username
                    await db.commit()
                log.info("Strategy 0 worked: direct ig_user_id", ig_user_id=ig_user_id)

        # Strategy 1: Use stored page_id if available
        if not ig_user_id and account.page_id:
            page_resp = await client.get(
                f"{settings.meta_base_url}/{account.page_id}",
                params={"fields": "instagram_business_account{id,username}", "access_token": token},
            )
            iba = page_resp.json().get("instagram_business_account")
            if iba and iba.get("id"):
                ig_user_id = iba["id"]
                ig_username = iba.get("username") or ig_username

        # Strategy 2: Scan all user pages (works even if page_id is null in DB)
        if not ig_user_id:
            me_resp = await client.get(
                f"{settings.meta_base_url}/me",
                params={"fields": "accounts{id,name,instagram_business_account{id,username}}", "access_token": token},
            )
            pages = me_resp.json().get("accounts", {}).get("data", [])
            for page in pages:
                iba = page.get("instagram_business_account")
                if iba and iba.get("id"):
                    ig_user_id = iba["id"]
                    ig_username = iba.get("username") or ig_username
                    # Auto-save to DB so next time is faster
                    account.page_id = page["id"]
                    account.page_name = page["name"]
                    account.ig_user_id = ig_user_id
                    account.ig_username = ig_username
                    await db.commit()
                    log.info("Auto-saved page+IG data from scan", page_id=page["id"], ig_user_id=ig_user_id)
                    break

        if not ig_user_id:
            raise HTTPException(
                status_code=400,
                detail="Instagram Business account nahi mila. Settings mein jaake Instagram connect/reconnect karo."
            )

        # Fetch media
        resp = await client.get(
            f"{settings.meta_base_url}/{ig_user_id}/media",
            params={
                "fields": "id,caption,media_type,media_url,thumbnail_url,permalink,like_count,comments_count,timestamp",
                "limit": 20,
                "access_token": token,
            },
        )
        data = resp.json()
        if "error" in data:
            log.error("Failed to fetch media", error=data["error"])
            raise HTTPException(status_code=400, detail=data["error"].get("message", "Posts load nahi ho sake"))

        return {
            "posts": data.get("data", []),
            "ig_username": ig_username,
            "ig_user_id": ig_user_id,
        }


@router.get("/accounts/{account_id}/capabilities", response_model=CapabilityResponse)
async def get_capabilities(
    account_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get capability matrix for an Instagram account."""
    result = await db.execute(
        select(InstagramAccount).where(
            InstagramAccount.id == account_id,
            InstagramAccount.user_id == current_user.id,
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    caps = CapabilityService.evaluate(account)
    return CapabilityResponse(
        capabilities=caps,
        permissions=list(account.permissions or {}).keys() if account.permissions else [],
    )


@router.delete("/accounts/{account_id}")
async def disconnect_account(
    account_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Disconnect an Instagram account."""
    result = await db.execute(
        select(InstagramAccount).where(
            InstagramAccount.id == account_id,
            InstagramAccount.user_id == current_user.id,
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    await db.delete(account)
    await db.commit()
    return {"status": "disconnected"}
