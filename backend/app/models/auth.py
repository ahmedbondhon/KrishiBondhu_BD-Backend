# ============================================================================
# KrishiBondhu Bangladesh — Auth ORM Models
# Maps to auth.* PostgreSQL tables (002_auth_tables.sql, alembic)
# ============================================================================

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base, TimestampMixin, UUIDPrimaryKeyMixin


# --------------------------------------------------------------------------
# auth.roles
# --------------------------------------------------------------------------
class Role(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Maps to auth.roles — system-defined user roles."""

    __tablename__ = "roles"
    __table_args__ = {"schema": "auth"}

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    users: Mapped[list["User"]] = relationship("User", back_populates="role", lazy="selectin")


# --------------------------------------------------------------------------
# auth.users
# --------------------------------------------------------------------------
class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Maps to auth.users — all platform users."""

    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}

    phone_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auth.roles.id", ondelete="RESTRICT"),
        nullable=False,
    )
    # Geo references
    division_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    district_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    upazila_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    union_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    village: Mapped[str | None] = mapped_column(String(200), nullable=True)

    preferred_language: Mapped[str] = mapped_column(String(10), server_default="bn", nullable=False)
    preferred_communication: Mapped[str] = mapped_column(String(20), server_default="sms", default="sms", nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[str] = mapped_column(
        String(30), server_default="active", nullable=False,
    )
    phone_verified: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    role: Mapped["Role"] = relationship("Role", back_populates="users", lazy="joined")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", lazy="selectin",
        cascade="all, delete-orphan",
    )
    login_attempts: Mapped[list["LoginAttempt"]] = relationship(
        "LoginAttempt", back_populates="user", lazy="noload",
        cascade="all, delete-orphan",
    )
    consents: Mapped[list["UserConsent"]] = relationship(
        "UserConsent", back_populates="user", lazy="selectin",
        cascade="all, delete-orphan",
    )

    @property
    def role_code(self) -> str:
        """Convenience: return the role code string."""
        return self.role.code if self.role else ""

    @property
    def effective_status(self) -> str:
        """Derive effective status from is_active/is_deleted/status fields."""
        if self.is_deleted:
            return "deleted"
        if not self.is_active:
            return "inactive"
        return self.status


# --------------------------------------------------------------------------
# auth.refresh_tokens
# --------------------------------------------------------------------------
class RefreshToken(UUIDPrimaryKeyMixin, Base):
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
    is_revoked: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")


# --------------------------------------------------------------------------
# auth.login_attempts
# --------------------------------------------------------------------------
class LoginAttempt(UUIDPrimaryKeyMixin, Base):
    """Tracks failed login attempts for lockout enforcement."""

    __tablename__ = "login_attempts"
    __table_args__ = {"schema": "auth"}

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="login_attempts")


# --------------------------------------------------------------------------
# auth.otp_logs
# --------------------------------------------------------------------------
class OtpLog(UUIDPrimaryKeyMixin, Base):
    """Maps to auth.otp_logs — OTP records with HMAC-hashed codes.

    Security:
      - otp_hash: HMAC-SHA256 of the OTP code (never store plain OTP)
      - verify_attempts: wrong-guess counter (max 5, then OTP is invalidated)
      - is_used: single-use flag (set True after successful verify)
    """

    __tablename__ = "otp_logs"
    __table_args__ = {"schema": "auth"}

    phone_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    otp_hash: Mapped[str] = mapped_column(String(128), nullable=False)  # HMAC-SHA256 hex
    purpose: Mapped[str] = mapped_column(String(50), server_default="registration", nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    verify_attempts: Mapped[int] = mapped_column(default=0, server_default="0", nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )


# --------------------------------------------------------------------------
# auth.consent_types
# --------------------------------------------------------------------------
class ConsentType(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Maps to auth.consent_types — Terms, Privacy, Location permission."""

    __tablename__ = "consent_types"
    __table_args__ = {"schema": "auth"}

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)

    user_consents: Mapped[list["UserConsent"]] = relationship("UserConsent", back_populates="consent_type")


# --------------------------------------------------------------------------
# auth.user_consents
# --------------------------------------------------------------------------
class UserConsent(UUIDPrimaryKeyMixin, Base):
    """Maps to auth.user_consents — user consent grant logs."""

    __tablename__ = "user_consents"
    __table_args__ = {"schema": "auth"}

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    consent_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auth.consent_types.id", ondelete="RESTRICT"),
        nullable=False,
    )
    is_granted: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="consents")
    consent_type: Mapped["ConsentType"] = relationship("ConsentType", back_populates="user_consents")


# --------------------------------------------------------------------------
# audit.admin_actions (Merged from models/audit.py)
# --------------------------------------------------------------------------
class AdminAction(UUIDPrimaryKeyMixin, Base):
    """Maps to audit.admin_actions — tracks administrative actions.

    Records:
      - actor_id: admin user who performed the action
      - action: e.g. "approve_user", "reject_user", "change_role"
      - target_id: user or resource affected
      - target_type: e.g. "user"
      - ip_address: client IP of the admin
      - details: JSON dictionary of change details
    """

    __tablename__ = "admin_actions"
    __table_args__ = {"schema": "audit"}

    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    target_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("timezone('utc', now())"),
        nullable=False,
    )

    actor = relationship("User", foreign_keys=[actor_id], lazy="joined")
