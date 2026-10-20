# ============================================================================
# KrishiBondhu Bangladesh — Auth & Geo Pydantic Schemas
# Request/Response DTOs for multi-step registration, OTP, login, and support
# ============================================================================

import re
import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from app.core.config import get_settings
from app.core.security import normalize_bd_phone

# --------------------------------------------------------------------------
# Constants & Validators
# --------------------------------------------------------------------------
OtpPurposeType = Literal["registration", "login", "reset_password"]
PreferredCommunicationType = Literal["sms", "call", "in_app"]

# Shared helper for backward compatibility and spec alignment
validate_bd_phone = normalize_bd_phone


# =========================================================================
# Step 1: OTP Request & Verification Schemas
# =========================================================================

class SendOtpRequest(BaseModel):
    """Request to generate and send an OTP code to a phone number."""

    model_config = ConfigDict(str_strip_whitespace=True)

    phone_number: str = Field(..., examples=["01712345678"])
    purpose: OtpPurposeType = Field(default="registration", examples=["registration"])

    @field_validator("phone_number")
    @classmethod
    def check_phone(cls, v: str) -> str:
        return validate_bd_phone(v)


class SendOtpResponse(BaseModel):
    """Response returned when an OTP is sent.

    SECURITY: OTP code is NEVER returned in the response.
    Use the SMS simulator popup in the frontend demo to see it.
    """

    message: str
    phone_number: str
    purpose: str
    expires_in_seconds: int
    resend_after: int = Field(
        default=60,
        description="Seconds to wait before requesting another OTP",
    )
    demo_mode: Optional[bool] = Field(
        default=None,
        description="True if demo OTP mode is enabled on the server",
    )


class VerifyOtpRequest(BaseModel):
    """Verify submitted OTP code for a given phone and purpose."""

    model_config = ConfigDict(str_strip_whitespace=True)

    phone_number: str = Field(..., examples=["01712345678"])
    otp_code: str = Field(..., min_length=4, max_length=10, examples=["123456"])
    purpose: OtpPurposeType = Field(default="registration")

    @field_validator("phone_number")
    @classmethod
    def check_phone(cls, v: str) -> str:
        return validate_bd_phone(v)


class VerifyOtpResponse(BaseModel):
    """Response returned when an OTP is successfully verified."""

    message: str
    phone_number: str
    is_verified: bool
    verification_token: str = Field(
        description="Signed token proving phone ownership for multi-step registration or password reset"
    )


def validate_farmer_pin(pin: str) -> str:
    """Password policy for farmers:
    - Numeric PIN only (digits 0-9)
    - Minimum length 6 (FARMER_PIN_MIN_LEN from config)
    """
    min_len = get_settings().farmer_pin_min_len
    if not pin.isdigit():
        raise ValueError("Farmer PIN must contain only numeric digits (0-9).")
    if len(pin) < min_len:
        raise ValueError(f"Farmer PIN must be at least {min_len} digits.")
    return pin


def validate_strong_password(password: str, role_name: str = "This role") -> str:
    """Password policy for privileged roles (Admin, Expert, Agent):
    - Minimum 8 characters (PRIVILEGED_PASSWORD_MIN_LEN from config)
    - At least one uppercase letter (A-Z)
    - At least one lowercase letter (a-z)
    - At least one digit (0-9)
    """
    min_len = get_settings().privileged_password_min_len
    if len(password) < min_len:
        raise ValueError(f"{role_name} password must be at least {min_len} characters long.")
    if not re.search(r"[A-Z]", password):
        raise ValueError(f"{role_name} password must contain at least one uppercase letter (A-Z).")
    if not re.search(r"[a-z]", password):
        raise ValueError(f"{role_name} password must contain at least one lowercase letter (a-z).")
    if not re.search(r"[0-9]", password):
        raise ValueError(f"{role_name} password must contain at least one digit (0-9).")
    return password


# =========================================================================
# Step 2 & 3: Registration Schemas
# =========================================================================

class FarmerAgentRegisterRequest(BaseModel):
    """Multi-step registration for farmer and agent roles."""

    model_config = ConfigDict(str_strip_whitespace=True)

    # Step 1: Mobile & Security
    phone_number: str = Field(..., examples=["01712345678"])
    otp_code: Optional[str] = Field(
        default=None,
        description="Direct OTP code entered, or verification_token from Step 1 verify",
    )
    verification_token: Optional[str] = Field(
        default=None,
        description="Signed verification token obtained from /auth/otp/verify",
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="Numeric PIN (min 6 digits) for farmers, or min 8 chars strong password for agents",
        examples=["123456"],
    )

    # Step 2: Personal & Role Details
    full_name: str = Field(..., min_length=2, max_length=150, examples=["মো. আব্দুর রহিম"])
    role: str = Field(default="farmer", examples=["farmer"])
    email: Optional[EmailStr] = Field(default=None, examples=["rahim@example.com"])

    # Step 2: Geographic Data
    division_id: Optional[uuid.UUID] = Field(default=None)
    district_id: Optional[uuid.UUID] = Field(default=None)
    upazila_id: Optional[uuid.UUID] = Field(default=None)
    union_id: Optional[uuid.UUID] = Field(default=None)
    village: Optional[str] = Field(default=None, max_length=200, examples=["দরিরামপুর"])

    # Fallback string fields if client sends text names
    district: Optional[str] = Field(default=None, max_length=100)
    upazila: Optional[str] = Field(default=None, max_length=100)

    # Preferences & Profile Media
    preferred_language: str = Field(default="bn", examples=["bn"])
    preferred_communication: PreferredCommunicationType = Field(
        default="sms",
        description="Preferred communication channel: sms, call, or in_app",
        examples=["sms"],
    )
    avatar_url: Optional[str] = Field(default=None, examples=["https://example.com/avatar.jpg"])

    # Step 3: Consents
    terms_accepted: bool = Field(
        default=True,
        description="Must be True to accept Terms of Service",
    )
    privacy_accepted: Optional[bool] = Field(
        default=None,
        description="Must be True to accept Privacy Policy (defaults to terms_accepted if omitted)",
    )
    location_permission_granted: bool = Field(
        default=False,
        description="User consent for GPS location tracking for weather & disease forecasts",
    )

    @field_validator("phone_number")
    @classmethod
    def check_phone(cls, v: str) -> str:
        return validate_bd_phone(v)

    @field_validator("role")
    @classmethod
    def check_role(cls, v: str) -> str:
        allowed = {"farmer", "agent", "expert"}
        if v not in allowed:
            raise ValueError(f"Self-registration allowed only for: {', '.join(allowed)}")
        return v

    @field_validator("preferred_language")
    @classmethod
    def check_language(cls, v: str) -> str:
        if v not in {"bn", "en"}:
            raise ValueError("Preferred language must be 'bn' (Bangla) or 'en' (English)")
        return v

    @model_validator(mode="after")
    def check_role_password_policy(self):
        if self.privacy_accepted is None:
            self.privacy_accepted = self.terms_accepted
        if self.role == "agent":
            validate_strong_password(self.password, "Agent")
        elif self.role == "farmer":
            validate_farmer_pin(self.password)
        return self


class ExpertRegisterRequest(BaseModel):
    """Registration for expert role — requires qualifications and admin approval."""

    model_config = ConfigDict(str_strip_whitespace=True)

    phone_number: str = Field(..., examples=["01912345678"])
    otp_code: Optional[str] = Field(default=None)
    verification_token: Optional[str] = Field(default=None)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=150, examples=["ড. আব্দুল করিম"])
    email: EmailStr = Field(..., examples=["karim@bari.gov.bd"])
    specialization: str = Field(..., max_length=200, examples=["Plant Pathology"])
    credentials: str = Field(..., max_length=500, examples=["PhD in Agriculture, BARI"])
    preferred_language: str = Field(default="bn")
    preferred_communication: PreferredCommunicationType = Field(
        default="sms",
        description="Preferred communication channel: sms, call, or in_app",
        examples=["sms"],
    )
    terms_accepted: bool = Field(default=True)
    privacy_accepted: Optional[bool] = Field(default=None)
    location_permission_granted: bool = Field(default=False)

    @model_validator(mode="after")
    def default_expert_privacy(self):
        if self.privacy_accepted is None:
            self.privacy_accepted = self.terms_accepted
        return self

    @field_validator("phone_number")
    @classmethod
    def check_phone(cls, v: str) -> str:
        return validate_bd_phone(v)

    @field_validator("password")
    @classmethod
    def check_expert_password(cls, v: str) -> str:
        return validate_strong_password(v, "Expert")


class AdminCreateUserRequest(BaseModel):
    """Admin-only user creation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr = Field(...)
    phone_number: str = Field(...)
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(..., examples=["admin", "administrator"])

    @field_validator("phone_number")
    @classmethod
    def check_phone(cls, v: str) -> str:
        return validate_bd_phone(v)

    @field_validator("password")
    @classmethod
    def check_admin_password(cls, v: str) -> str:
        return validate_strong_password(v, "Admin")

    @field_validator("role")
    @classmethod
    def check_role(cls, v: str) -> str:
        allowed = {"administrator", "technical_admin", "admin"}
        if v not in allowed:
            raise ValueError(f"Admin creation only for: {', '.join(allowed)}")
        return v


# =========================================================================
# Login Schemas (Password/PIN + Passwordless OTP)
# =========================================================================

class LoginRequest(BaseModel):
    """Login with phone_number OR email + password/PIN, with 'remember_me'."""

    model_config = ConfigDict(str_strip_whitespace=True)

    phone_number: Optional[str] = Field(default=None, examples=["01712345678"])
    email: Optional[EmailStr] = Field(default=None, examples=["rahim@example.com"])
    password: str = Field(..., min_length=1, description="Password or 4-6 digit PIN")
    remember_me: bool = Field(
        default=False,
        description="If True, issues extended refresh token (30 days instead of 7 days)",
    )

    @model_validator(mode="after")
    def require_identifier(self):
        if not self.phone_number and not self.email:
            raise ValueError("Either phone_number or email is required")
        return self

    @field_validator("phone_number")
    @classmethod
    def check_phone(cls, v: str | None) -> str | None:
        if v is not None:
            return validate_bd_phone(v)
        return v


class OtpLoginRequest(BaseModel):
    """Request OTP for passwordless login."""

    model_config = ConfigDict(str_strip_whitespace=True)

    phone_number: str = Field(..., examples=["01712345678"])

    @field_validator("phone_number")
    @classmethod
    def check_phone(cls, v: str) -> str:
        return validate_bd_phone(v)


class OtpLoginVerifyRequest(BaseModel):
    """Verify OTP and complete passwordless login."""

    model_config = ConfigDict(str_strip_whitespace=True)

    phone_number: str = Field(..., examples=["01712345678"])
    otp_code: str = Field(..., min_length=4, max_length=10, examples=["123456"])
    remember_me: bool = Field(default=False)

    @field_validator("phone_number")
    @classmethod
    def check_phone(cls, v: str) -> str:
        return validate_bd_phone(v)


# =========================================================================
# Password Reset (Forgot Password) Schemas
# =========================================================================

class ForgotPasswordRequest(BaseModel):
    """Request OTP to reset password or PIN."""

    model_config = ConfigDict(str_strip_whitespace=True)

    phone_number: str = Field(..., examples=["01712345678"])

    @field_validator("phone_number")
    @classmethod
    def check_phone(cls, v: str) -> str:
        return validate_bd_phone(v)


class ResetPasswordRequest(BaseModel):
    """Reset password or PIN using verified OTP or verification token."""

    model_config = ConfigDict(str_strip_whitespace=True)

    phone_number: str = Field(..., examples=["01712345678"])
    otp_code: Optional[str] = Field(default=None, examples=["123456"])
    verification_token: Optional[str] = Field(default=None)
    new_password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="New password (min 8 chars strong for privileged roles) or numeric PIN (min 6 digits for farmers)",
    )

    @field_validator("phone_number")
    @classmethod
    def check_phone(cls, v: str) -> str:
        return validate_bd_phone(v)

    @field_validator("new_password")
    @classmethod
    def check_password_strength(cls, v: str) -> str:
        min_len = get_settings().farmer_pin_min_len
        if len(v) < min_len:
            raise ValueError(f"New password/PIN must be at least {min_len} characters/digits.")
        return v


# =========================================================================
# Preferences & Language
# =========================================================================

class UpdateLanguageRequest(BaseModel):
    """Toggle language preference between Bangla (bn) and English (en)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    preferred_language: str = Field(..., examples=["bn"])

    @field_validator("preferred_language")
    @classmethod
    def check_language(cls, v: str) -> str:
        if v not in {"bn", "en"}:
            raise ValueError("preferred_language must be 'bn' or 'en'")
        return v


# =========================================================================
# Response DTOs
# =========================================================================

def get_dashboard_path_for_role(role: str) -> str:
    """Map role code to frontend dashboard redirect path.

    - farmer -> /dashboard
    - agent -> /agent/dashboard
    - expert -> /expert/dashboard
    - administrator -> /admin/dashboard
    """
    mapping = {
        "farmer": "/dashboard",
        "agent": "/agent/dashboard",
        "expert": "/expert/dashboard",
        "administrator": "/admin/dashboard",
        "admin": "/admin/dashboard",
        "technical_admin": "/admin/dashboard",
    }
    return mapping.get(role, "/dashboard")


class UserResponse(BaseModel):
    """Public user representation returned by API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    phone_number: str
    email: Optional[str] = None
    role: str = Field(description="Role code (e.g. 'farmer', 'expert', 'agent', 'administrator')")
    status: str
    preferred_language: str
    preferred_communication: str = Field(default="sms", description="Preferred channel: sms, call, in_app")
    avatar_url: Optional[str] = None
    division_id: Optional[uuid.UUID] = None
    district_id: Optional[uuid.UUID] = None
    upazila_id: Optional[uuid.UUID] = None
    union_id: Optional[uuid.UUID] = None
    village: Optional[str] = None
    phone_verified: bool
    email_verified: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    dashboard_path: str = Field(default="/dashboard", description="Role-based frontend redirect dashboard path")

    @model_validator(mode="after")
    def set_dashboard_path(self):
        if not self.dashboard_path or self.dashboard_path == "/dashboard":
            if self.role:
                self.dashboard_path = get_dashboard_path_for_role(self.role)
        return self


class UserDetailResponse(UserResponse):
    """Extended user detail (admin view)."""

    is_active: bool
    is_deleted: bool
    updated_at: Optional[datetime] = None


class TokenResponse(BaseModel):
    """JWT token pair returned on successful login / refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token TTL in seconds")
    user: Optional[UserResponse] = None
    dashboard_path: Optional[str] = Field(default=None, description="Role-based frontend dashboard redirect path")

    @model_validator(mode="after")
    def set_dashboard_path(self):
        if not self.dashboard_path and self.user and self.user.role:
            self.dashboard_path = get_dashboard_path_for_role(self.user.role)
        return self


class RefreshTokenRequest(BaseModel):
    """Request to rotate a refresh token."""

    refresh_token: str


class LogoutRequest(BaseModel):
    """Request to revoke a refresh token on logout."""

    refresh_token: str


class RegisterResponse(BaseModel):
    """Response returned after successful registration."""

    message: str
    user: UserResponse
    tokens: Optional[TokenResponse] = None
    dashboard_path: Optional[str] = Field(default=None, description="Role-based frontend dashboard redirect path")

    @model_validator(mode="after")
    def set_dashboard_path(self):
        if not self.dashboard_path and self.user and self.user.role:
            self.dashboard_path = get_dashboard_path_for_role(self.user.role)
        return self


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str


class MeResponse(UserResponse):
    """Current authenticated user profile."""
    pass


class SupportContactResponse(BaseModel):
    """Helpline & Call Support information."""

    helpline_number: str = Field(description="Shortcode helpline (e.g., 16123)")
    support_phone: str = Field(description="Direct phone support number")
    support_email: str = Field(description="Official support email")
    available_hours_bn: str
    available_hours_en: str
    call_center_role: str = "agent"
    title_bn: str = "কৃষিবন্ধু সহায়তা ও কল সেন্টার"
    title_en: str = "KrishiBondhu Support & Call Center"
    instructions_bn: str = "যে কোনো কারিগরি বা কৃষি পরামর্শের জন্য সরাসরি কল সেন্টারে যোগাযোগ করুন।"
    instructions_en: str = "For any technical or agricultural advisory, contact our call center directly."


# =========================================================================
# Geo Dropdown Responses
# =========================================================================

class GeoItem(BaseModel):
    """Geographic entity representation for cascading dropdowns."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    bbs_code: str
    name_en: str
    name_bn: str


class DivisionResponse(GeoItem):
    pass


class DistrictResponse(GeoItem):
    division_id: uuid.UUID


class UpazilaResponse(GeoItem):
    district_id: uuid.UUID


class UnionResponse(GeoItem):
    upazila_id: uuid.UUID
