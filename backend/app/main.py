"""
Instagram Automation Platform — FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.database import create_tables
from app.core.logging_config import configure_logging

# ── Routers ──────────────────────────────────────────────────────
from app.api import (
    auth,
    automations,
    campaigns,
    contacts,
    instagram,
    links,
    logs,
    settings as settings_router,
    webhooks,
    analytics,
    inbox,
    tags,
)

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    configure_logging()
    log.info("Starting Instagram Automation Platform", env=settings.APP_ENV)
    await create_tables()
    log.info("Database tables verified")
    yield
    log.info("Shutting down")


# ── Rate Limiter ──────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"])

# ── App ───────────────────────────────────────────────────────────
app = FastAPI(
    title="Instagram Automation Platform",
    description="Production-grade Instagram automation with Meta API integration",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/api/redoc" if settings.APP_ENV != "production" else None,
    openapi_url="/api/openapi.json" if settings.APP_ENV != "production" else None,
)

# ── Middleware ────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────
API_PREFIX = "/api"

app.include_router(auth.router, prefix=f"{API_PREFIX}/auth", tags=["Authentication"])
app.include_router(instagram.router, prefix=f"{API_PREFIX}/instagram", tags=["Instagram"])
app.include_router(automations.router, prefix=f"{API_PREFIX}/automations", tags=["Automations"])
app.include_router(campaigns.router, prefix=f"{API_PREFIX}/campaigns", tags=["Campaigns"])
app.include_router(contacts.router, prefix=f"{API_PREFIX}/contacts", tags=["Contacts"])
app.include_router(tags.router, prefix=f"{API_PREFIX}/tags", tags=["Tags"])
app.include_router(links.router, prefix=f"{API_PREFIX}/links", tags=["Links"])
app.include_router(inbox.router, prefix=f"{API_PREFIX}/inbox", tags=["Inbox"])
app.include_router(analytics.router, prefix=f"{API_PREFIX}/analytics", tags=["Analytics"])
app.include_router(logs.router, prefix=f"{API_PREFIX}/logs", tags=["Logs"])
app.include_router(settings_router.router, prefix=f"{API_PREFIX}/settings", tags=["Settings"])
app.include_router(webhooks.router, prefix=f"{API_PREFIX}/webhooks", tags=["Webhooks"])


@app.api_route("/api/health", methods=["GET", "HEAD"], tags=["Health"])
async def health():
    return {"status": "ok", "version": "1.0.0", "env": settings.APP_ENV}
