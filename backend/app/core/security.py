# ============================================================================
# KrishiBondhu Bangladesh — Core Security, Cryptography & Rate Limiting
# ============================================================================

import hashlib
import hmac
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from fastapi import Request
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import get_settings

settings = get_settings()


# ============================================================================
# 1. Phone Normalization & Validation
# ============================================================================

# Bangladesh standard mobile number format: 01XXXXXXXXX (11 digits, operator prefix 013-019)
BD_PHONE_REGEX = re.compile(r"^01[3-9]\d{8}$")


def normalize_bd_phone(phone: str) -> str:
    """Normalize and validate a Bangladesh phone number.

    Accepts:
      - 01XXXXXXXXX
      - 8801XXXXXXXXX
      - +8801XXXXXXXXX

    Normalizes to:
      01XXXXXXXXX (11 digits)
    """
    if not phone or not isinstance(phone, str):
        raise ValueError("Phone number must be a non-empty string.")

    cleaned = phone.strip().replace(" ", "").replace("-", "")
    if cleaned.startswith("+88"):
        cleaned = cleaned[3:]
    elif cleaned.startswith("88"):
        cleaned = cleaned[2:]

    if not BD_PHONE_REGEX.match(cleaned):
        raise ValueError(
            "Invalid Bangladesh phone number. Expected 11 digits starting with 013-019 (e.g., 01712345678)"
        )
    return cleaned


# ============================================================================
# 2. Password & OTP Hashing
# ============================================================================

def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt with auto-generated salt."""
    pwd_bytes = plain_password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def generate_numeric_otp(length: int = 6) -> str:
    """Generate cryptographically secure numeric OTP of specified length."""
    if length <= 0:
        raise ValueError("OTP length must be positive")
    return "".join([str(secrets.randbelow(10)) for _ in range(length)])


def hmac_hash_otp(otp_code: str, secret: str) -> str:
    """Create HMAC-SHA256 hex digest of an OTP code."""
    return hmac.new(
        key=secret.encode("utf-8"),
        msg=otp_code.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()


def hmac_verify_otp(otp_code: str, otp_hash: str, secret: str) -> bool:
    """Constant-time comparison of OTP code against stored HMAC hash."""
    computed = hmac_hash_otp(otp_code, secret)
    return hmac.compare_digest(computed, otp_hash)


# ============================================================================
# 3. JWT Token Helpers
# ============================================================================

def create_access_token(
    user_id: uuid.UUID,
    role: str,
    status: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a short-lived JWT access token."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "status": status,
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(
    user_id: uuid.UUID,
    expires_delta: timedelta | None = None,
) -> tuple[str, datetime]:
    """Create a refresh token and return (token_string, expires_at)."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=settings.refresh_token_expire_days))

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "iat": now,
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4()),  # unique token id for one-use enforcement
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expire


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token. Raises JWTError on failure."""
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


def decode_token_safe(token: str) -> dict[str, Any] | None:
    """Decode a JWT without raising — returns None on failure."""
    try:
        return decode_token(token)
    except JWTError:
        return None


# ============================================================================
# 4. Rate Limiter (slowapi)
# ============================================================================

limiter = Limiter(key_func=get_remote_address)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return 429 Too Many Requests with Retry-After header."""
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}. Please try again later."},
        headers={"Retry-After": "600"},
    )
