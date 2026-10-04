"""
Security utilities: JWT tokens, password hashing, token encryption.
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from cryptography.fernet import Fernet
from jose import JWTError, jwt
import bcrypt
from app.core.config import settings

# ── Password Hashing ─────────────────────────────────────────────

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except ValueError:
        return False


# ── JWT ──────────────────────────────────────────────────────────
ALGORITHM = "HS256"


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {"sub": subject, "type": "access", "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": subject, "type": "refresh", "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT. Raises JWTError on failure."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])


# ── Token Encryption (for Meta access tokens stored in DB) ────────
_fernet = Fernet(settings.ENCRYPTION_KEY.encode())


def encrypt_token(value: str) -> str:
    """Encrypt a sensitive string (e.g., Meta access token) for storage."""
    return _fernet.encrypt(value.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    """Decrypt a previously encrypted token."""
    return _fernet.decrypt(encrypted.encode()).decode()


# ── Secure Random Tokens ──────────────────────────────────────────
def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure URL-safe token."""
    return secrets.token_urlsafe(length)


def generate_webhook_verify_token() -> str:
    return generate_secure_token(24)
