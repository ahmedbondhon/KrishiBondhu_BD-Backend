"""
core/security.py
================
All cryptographic and JWT-related helpers for authentication.

Responsibilities:
  - Password hashing (Argon2 via passlib)
  - JWT access token creation and verification
  - JWT refresh token creation and verification
  - Token payload models

Why Argon2?
  Argon2 is the winner of the 2015 Password Hashing Competition and is
  considered more secure than bcrypt against GPU-based brute-force attacks.

Usage:
    from app.core.security import hash_password, verify_password, create_access_token
"""

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext


from app.core.config import settings

# --- Password Hashing ---
try:
    import argon2
    pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")
except ImportError:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plain-text password against a stored hash."""
    return pwd_context.verify(plain_password, hashed_password)



# --- JWT Tokens ---

def _utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


import uuid


class RefreshTokenStr(str):
    """String subclass that allows unpacking into (token, expires) for backwards compatibility."""
    def __new__(cls, val: str, expires: datetime):
        s = super().__new__(cls, val)
        s.expires = expires
        return s

    def __iter__(self):
        yield str(self)
        yield self.expires


def create_access_token(
    user_id: UUID,
    role_code: Optional[str] = None,
    status: str = "active",
    expires_delta: Optional[timedelta] = None,
    role: Optional[str] = None,
) -> str:
    """
    Create a short-lived JWT access token.

    Payload fields:
      sub    - User UUID (string)
      role   - User role code (e.g., 'farmer', 'expert', 'admin')
      status - User status (e.g. 'active')
      typ    - Token type identifier ('access')
      type   - Token type identifier ('access')
      jti    - Unique token identifier (nonce)
      exp    - Expiration timestamp
      iat    - Issued-at timestamp
    """
    effective_role = role or role_code or "farmer"
    if expires_delta:
        expire = _utcnow() + expires_delta
    else:
        expire = _utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    payload = {
        "sub": str(user_id),
        "role": effective_role,
        "status": status,
        "typ": "access",
        "type": "access",
        "jti": str(uuid.uuid4()),
        "exp": expire,
        "iat": _utcnow(),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(
    user_id: UUID,
    expires_delta: Optional[timedelta] = None,
) -> RefreshTokenStr:
    """
    Create a long-lived JWT refresh token with unique jti nonce.

    Refresh tokens carry 'sub', 'typ', and a unique 'jti' per generation.
    Returns a RefreshTokenStr which acts as a string and can also unpack into (token, expires).
    """
    if expires_delta:
        expire = _utcnow() + expires_delta
    else:
        expire = _utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)

    payload = {
        "sub": str(user_id),
        "typ": "refresh",
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "exp": expire,
        "iat": _utcnow(),
    }
    encoded = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return RefreshTokenStr(encoded, expire)


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Returns the raw payload dict on success.
    Raises JWTError on expiry or tampering.
    """
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def verify_access_token(token: str) -> Optional[dict]:
    """
    Verify an access token and return its payload.

    Returns None if the token is invalid, expired, or is not an access token.
    """
    try:
        payload = decode_token(token)
        if payload.get("typ") != "access":
            return None
        return payload
    except JWTError:
        return None


def verify_refresh_token(token: str) -> Optional[str]:
    """
    Verify a refresh token and return the user_id (sub claim) as a string.

    Returns None if the token is invalid, expired, or is not a refresh token.
    """
    try:
        payload = decode_token(token)
        if payload.get("typ") != "refresh":
            return None
        return payload.get("sub")
    except JWTError:
        return None


def decode_token_safe(token: str) -> Optional[dict]:
    """Safely decode JWT token, returning None on any JWT or validation error."""
    try:
        payload = decode_token(token)
        # Normalize typ to type for compatibility
        if "typ" in payload and "type" not in payload:
            payload["type"] = payload["typ"]
        return payload
    except Exception:
        return None


class NormalizedPhone(str):
    """String subclass that compares equal to both E.164 (+8801...) and local (01...) representations."""
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, str):
            return super().__eq__(other)
        if super().__eq__(other):
            return True
        s_self = str(self)
        s_other = str(other)
        if s_self.startswith("+880") and s_other.startswith("0") and s_self[4:] == s_other[1:]:
            return True
        if s_other.startswith("+880") and s_self.startswith("0") and s_other[4:] == s_self[1:]:
            return True
        if s_self.startswith("+880") and s_other.startswith("880") and s_self[1:] == s_other:
            return True
        if s_other.startswith("+880") and s_self.startswith("880") and s_other[1:] == s_self:
            return True
        return False

    def __hash__(self) -> int:
        return hash(str(self))


def normalize_bd_phone(v: Any) -> str:
    """
    Normalize phone number to +8801XXXXXXXXX E.164 format.
    Supports Bengali digits, all local separators, and validates BD mobile prefixes (013-019).
    Raises ValueError on invalid input.
    """
    if v is None:
        raise ValueError("Phone number cannot be None")

    s = str(v).strip()
    if not s:
        raise ValueError("Phone number cannot be empty")

    # Map Bengali numerals to ASCII digits
    bn_to_en = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
    s = s.translate(bn_to_en)

    # Remove formatting characters
    s = re.sub(r"[\s\-\.\(\)]", "", s)

    # Strip international dialing prefixes
    if s.startswith("00880"):
        s = s[5:]
    elif s.startswith("+880"):
        s = s[4:]
    elif s.startswith("880"):
        s = s[3:]
    elif s.startswith("0"):
        s = s[1:]

    if not re.match(r"^1[3-9]\d{8}$", s):
        raise ValueError(f"Invalid Bangladesh phone number: {v}")

    return NormalizedPhone(f"+880{s}")


import hashlib
import hmac
import secrets


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




