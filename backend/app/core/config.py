"""
Central configuration — all values loaded from environment variables.
Never hardcode secrets here.
"""
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "Instagram Automation Platform"
    APP_ENV: str = "development"
    BASE_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"
    SECRET_KEY: str
    ENCRYPTION_KEY: str

    # ── Database ─────────────────────────────────────────────────
    DATABASE_URL: str

    # ── Redis ────────────────────────────────────────────────────
    REDIS_URL: str
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    # ── Meta / Instagram ─────────────────────────────────────────
    META_APP_ID: Optional[str] = None
    META_APP_SECRET: Optional[str] = None
    META_WEBHOOK_VERIFY_TOKEN: Optional[str] = None
    META_WEBHOOK_URL: Optional[str] = None
    META_API_VERSION: str = "v21.0"

    # ── Auth ─────────────────────────────────────────────────────
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Admin ────────────────────────────────────────────────────
    ADMIN_EMAIL: Optional[str] = None
    ADMIN_PASSWORD: Optional[str] = None

    # ── CORS ─────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # ── Rate Limiting ─────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60
    DM_RATE_LIMIT_PER_HOUR: int = 200

    # ── Logging ──────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = False

    # ── Link Domain ──────────────────────────────────────────────
    LINK_DOMAIN: Optional[str] = None

    @property
    def CORS_ORIGINS_LIST(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def effective_broker_url(self) -> str:
        return self.CELERY_BROKER_URL or self.REDIS_URL.replace("/0", "/1")

    @property
    def effective_result_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL.replace("/0", "/2")

    @property
    def effective_link_domain(self) -> str:
        return self.LINK_DOMAIN or self.BASE_URL

    @property
    def meta_base_url(self) -> str:
        return f"https://graph.facebook.com/{self.META_API_VERSION}"

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_not_default(cls, v: str) -> str:
        if "CHANGE_ME" in v or len(v) < 32:
            raise ValueError("SECRET_KEY must be set to a secure random value (min 32 chars)")
        return v

    @field_validator("ENCRYPTION_KEY")
    @classmethod
    def encryption_key_not_default(cls, v: str) -> str:
        if "CHANGE_ME" in v:
            raise ValueError("ENCRYPTION_KEY must be set to a valid Fernet key")
        return v


settings = Settings()
