"""
schemas/auth.py
===============
Pydantic v2 request and response schemas for authentication endpoints.

Naming convention:
  - *Request : Incoming data from the client (validated on entry)
  - *Response: Outgoing data to the client (serialized from ORM models)

All schemas use `model_config = ConfigDict(from_attributes=True)` to allow
direct creation from SQLAlchemy ORM model instances (replaces Pydantic v1's `orm_mode`).
"""

from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ─────────────────────────────────────────────────────────
# Registration & Login
# ─────────────────────────────────────────────────────────

def normalize_bangladesh_phone(v: Any) -> str:
    """Normalize Bangladeshi phone numbers into canonical E.164 (+880XXXXXXXXXX) format."""
    if not isinstance(v, str):
        v = str(v)
    v = v.strip().replace(" ", "").replace("-", "")
    if v.startswith("01"):
        v = "+88" + v
    elif v.startswith("880"):
        v = "+" + v
    elif not v.startswith("+") and v.startswith("1"):
        v = "+880" + v
    return v


class RegisterRequest(BaseModel):
    """POST /api/v1/auth/register — New user registration payload."""
    phone_number: str = Field(..., pattern=r"^\+880\d{10}$", description="Bangladesh phone number: +8801XXXXXXXXX")
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=150)
    role_code: Literal["farmer"] = Field(default="farmer", description="Role: farmer only for public registration")

    @field_validator("phone_number", mode="before")
    @classmethod
    def normalize_phone(cls, v: Any) -> str:
        return normalize_bangladesh_phone(v)


class LoginRequest(BaseModel):
    """POST /api/v1/auth/login — Login with phone number and password."""
    phone_number: str = Field(..., description="Registered phone number")
    password: str = Field(..., min_length=1)

    @field_validator("phone_number", mode="before")
    @classmethod
    def normalize_phone(cls, v: Any) -> str:
        return normalize_bangladesh_phone(v)


class RefreshTokenRequest(BaseModel):
    """POST /api/v1/auth/refresh — Exchange refresh token for new access token."""
    refresh_token: str


# ─────────────────────────────────────────────────────────
# Token Responses
# ─────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    """Returned on successful login or token refresh."""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in_minutes: int


# ─────────────────────────────────────────────────────────
# User Profile
# ─────────────────────────────────────────────────────────

class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    code: str
    name: str


class UserResponse(BaseModel):
    """Returned by GET /api/v1/auth/me and registration."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    phone_number: str
    full_name: str
    role: RoleResponse
    preferred_language: str
    avatar_url: Optional[str] = None
    division_id: Optional[UUID] = None
    district_id: Optional[UUID] = None
    upazila_id: Optional[UUID] = None
    union_id: Optional[UUID] = None
    is_active: bool


class UpdateProfileRequest(BaseModel):
    """POST /api/v1/farmers/me/profile — Update farmer geographic and communication profile."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=150)
    division_id: Optional[UUID] = None
    district_id: Optional[UUID] = None
    upazila_id: Optional[UUID] = None
    union_id: Optional[UUID] = None
    preferred_language: Optional[str] = Field(None, pattern="^(bn|en)$")
    avatar_url: Optional[str] = None
