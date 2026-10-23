"""
models/auth.py
==============
SQLAlchemy ORM models for the `auth` schema.

Tables mapped here:
  - auth.roles       → Role
  - auth.users       → User
  - auth.user_consents → UserConsent
  - auth.consent_types → ConsentType
  - auth.otp_logs    → OtpLog

These models are the foundation of authentication and authorization.
Every User has exactly one Role (farmer, agent, expert, admin, tech_admin).
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Role(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    auth.roles — Defines the user roles available in the system.

    Seeded roles (see database/migrations/014_seed_data.sql):
      - farmer     : End-user farmers submitting crop diagnosis requests
      - agent      : Field agents assisting farmers
      - expert     : Agricultural experts who review AI diagnosis
      - admin      : Platform administrators
      - tech_admin : Technical system administrators
    """
    __tablename__ = "roles"
    __table_args__ = {"schema": "auth"}

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="role")


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    auth.users — All registered users across roles.

    Phone number is the primary identifier (Bangladesh mobile-first).
    Geo location fields (division_id, district_id, etc.) are FK references
    to the geo schema, populated when a farmer sets up their profile.
    """
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}

    phone_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("auth.roles.id", ondelete="RESTRICT"), nullable=False)

    # Geographic profile (optional, set during profile setup)
    # Note: DB-level FK constraints exist in SQL migrations; no ORM geo models needed.
    division_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    district_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    upazila_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    union_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    preferred_language: Mapped[str] = mapped_column(String(10), default="bn", nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Extended profile and verification fields
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    village: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    preferred_communication: Mapped[str] = mapped_column(String(20), default="sms", nullable=False)

    # Relationships
    role: Mapped["Role"] = relationship("Role", back_populates="users")
    consents: Mapped[List["UserConsent"]] = relationship("UserConsent", back_populates="user")
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    login_attempts: Mapped[List["LoginAttempt"]] = relationship("LoginAttempt", back_populates="user", cascade="all, delete-orphan")

    @property
    def effective_status(self) -> str:
        if self.is_deleted:
            return "deleted"
        if not self.is_active:
            return "inactive"
        return self.status


    @property
    def role_code(self) -> str:
        if self.role:
            return self.role.code
        return "farmer"



class ConsentType(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    auth.consent_types — Defines the types of consent a user can grant.

    Seeded types: account_terms, image_processing, location_data, ai_improvement.
    """
    __tablename__ = "consent_types"
    __table_args__ = {"schema": "auth"}

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user_consents: Mapped[List["UserConsent"]] = relationship("UserConsent", back_populates="consent_type")


class UserConsent(Base, UUIDPrimaryKeyMixin):
    """
    auth.user_consents — Audit trail of user consent decisions.

    Immutable records: once a consent is granted or revoked, a new record is added.
    """
    __tablename__ = "user_consents"
    __table_args__ = {"schema": "auth"}

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False)
    consent_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("auth.consent_types.id", ondelete="RESTRICT"), nullable=False)
    is_granted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="consents")
    consent_type: Mapped["ConsentType"] = relationship("ConsentType", back_populates="user_consents")


class OtpLog(Base, UUIDPrimaryKeyMixin):
    """
    auth.otp_logs — SMS OTP verification log for phone-based auth.
    """
    __tablename__ = "otp_logs"
    __table_args__ = {"schema": "auth"}

    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    otp_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    otp_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    purpose: Mapped[str] = mapped_column(String(50), default="registration", nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verify_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)


class RefreshToken(Base, UUIDPrimaryKeyMixin):
    """Stores issued refresh tokens for rotation and revocation."""
    __tablename__ = "refresh_tokens"
    __table_args__ = {"schema": "auth"}

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")


class LoginAttempt(Base, UUIDPrimaryKeyMixin):
    """Tracks failed login attempts for lockout enforcement."""
    __tablename__ = "login_attempts"
    __table_args__ = {"schema": "auth"}

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="login_attempts")



class AdminAction(Base, UUIDPrimaryKeyMixin):
    """Tracks administrative actions."""
    __tablename__ = "admin_actions"
    __table_args__ = {"schema": "audit"}

    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    target_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), server_default=func.now(), nullable=False)

