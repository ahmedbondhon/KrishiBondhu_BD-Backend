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

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# --- Password Hashing ---
# Argon2 is the primary scheme; bcrypt is kept as a fallback for migrations.
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using Argon2."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plain-text password against a stored Argon2 hash."""
    return pwd_context.verify(plain_password, hashed_password)


# --- JWT Tokens ---

def _utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


def create_access_token(user_id: UUID, role_code: str) -> str:
    """
    Create a short-lived JWT access token.

    Payload fields:
      sub  - User UUID (string)
      role - User role code (e.g., 'farmer', 'expert', 'admin')
      typ  - Token type identifier ('access')
      exp  - Expiration timestamp
      iat  - Issued-at timestamp
    """
    expire = _utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "role": role_code,
        "typ": "access",
        "exp": expire,
        "iat": _utcnow(),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: UUID) -> str:
    """
    Create a long-lived JWT refresh token.

    Refresh tokens only carry the 'sub' and 'typ' claims.
    They are used ONLY to issue new access tokens (see /api/v1/auth/refresh).
    """
    expire = _utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)
    payload = {
        "sub": str(user_id),
        "typ": "refresh",
        "exp": expire,
        "iat": _utcnow(),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


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
