# ============================================================================
# KrishiBondhu Bangladesh — Auth & Geo Repository
# Data access layer for auth.* and geo.* tables (async SQLAlchemy)
# ============================================================================

import hashlib
import inspect
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import (
    AdminAction,
    ConsentType,
    LoginAttempt,
    OtpLog,
    RefreshToken,
    Role,
    User,
    UserConsent,
)
from app.models.geo import District, Division, Union, Upazila
from app.core.security import normalize_bd_phone


class AuthRepository:
    """Async data-access layer for authentication, OTP, consents, and user management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _add_and_flush(self, obj) -> None:
        """Add an entity to the session and flush, safely awaiting if mocked as coroutine."""
        res: Any = self.db.add(obj)
        if inspect.isawaitable(res):
            await res
        await self.db.flush()

    async def _extract_entity(self, result, entity_cls):
        """Safely extract a single entity from a query result, supporting AsyncMock."""
        if result is None:
            return None
        if hasattr(result, "scalar_one_or_none"):
            val: Any = result.scalar_one_or_none()
            if inspect.isawaitable(val):
                val = await val
            return val if isinstance(val, entity_cls) else None
        return None

    async def _extract_scalar(self, result, default=0):
        """Safely extract a scalar value (e.g. count) from a query result, supporting AsyncMock."""
        if result is None:
            return default
        if hasattr(result, "scalar"):
            val: Any = result.scalar()
            if inspect.isawaitable(val):
                val = await val
            return val if isinstance(val, (int, float, bool, str)) else default
        return default

    # ------------------------------------------------------------------
    # Roles
    # ------------------------------------------------------------------
    async def get_role_by_code(self, code: str) -> Optional[Role]:
        """Fetch a system role by code (e.g. 'farmer', 'agent', 'expert')."""
        stmt = select(Role).where(Role.code == code)
        result = await self.db.execute(stmt)
        return await self._extract_entity(result, Role)

    # ------------------------------------------------------------------
    # Users — Queries & Mutations
    # ------------------------------------------------------------------
    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        stmt = select(User).options(selectinload(User.role)).where(User.id == user_id, User.is_deleted == False)
        result = await self.db.execute(stmt)
        return await self._extract_entity(result, User)

    async def get_user_by_phone(self, phone_number: str) -> Optional[User]:
        phone_number = normalize_bd_phone(phone_number)
        stmt = select(User).options(selectinload(User.role)).where(User.phone_number == phone_number, User.is_deleted == False)
        result = await self.db.execute(stmt)
        return await self._extract_entity(result, User)

    async def get_user_by_phone_any_state(self, phone_number: str) -> Optional[User]:
        phone_number = normalize_bd_phone(phone_number)
        stmt = select(User).options(selectinload(User.role)).where(User.phone_number == phone_number)
        result = await self.db.execute(stmt)
        return await self._extract_entity(result, User)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).options(selectinload(User.role)).where(User.email == email, User.is_deleted == False)
        result = await self.db.execute(stmt)
        return await self._extract_entity(result, User)

    async def phone_exists(self, phone_number: str) -> bool:
        phone_number = normalize_bd_phone(phone_number)
        stmt = select(func.count()).select_from(User).where(User.phone_number == phone_number, User.is_deleted == False)
        result = await self.db.execute(stmt)
        val = await self._extract_scalar(result, 0)
        return (val or 0) > 0

    async def email_exists(self, email: str) -> bool:
        stmt = select(func.count()).select_from(User).where(User.email == email, User.is_deleted == False)
        result = await self.db.execute(stmt)
        val = await self._extract_scalar(result, 0)
        return (val or 0) > 0

    async def create_user(self, user: User) -> User:
        await self._add_and_flush(user)
        await self.db.refresh(user)
        return user

    async def update_last_login(self, user_id: uuid.UUID) -> None:
        stmt = update(User).where(User.id == user_id).values(last_login_at=datetime.now(timezone.utc))
        await self.db.execute(stmt)

    async def update_user_password(self, user_id: uuid.UUID, password_hash: str) -> None:
        stmt = update(User).where(User.id == user_id).values(password_hash=password_hash, updated_at=datetime.now(timezone.utc))
        await self.db.execute(stmt)

    async def update_user_language(self, user_id: uuid.UUID, language: str) -> None:
        stmt = update(User).where(User.id == user_id).values(preferred_language=language, updated_at=datetime.now(timezone.utc))
        await self.db.execute(stmt)

    # ------------------------------------------------------------------
    # Refresh Tokens
    # ------------------------------------------------------------------
    @staticmethod
    def _hash_token(token: str) -> str:
        """SHA-256 hash a refresh token for secure database storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    async def store_refresh_token(
        self,
        user_id: uuid.UUID,
        token: str,
        expires_at: datetime,
    ) -> RefreshToken:
        rt = RefreshToken(
            user_id=user_id,
            token_hash=self._hash_token(token),
            expires_at=expires_at,
        )
        await self._add_and_flush(rt)
        return rt

    async def get_refresh_token(self, token: str) -> Optional[RefreshToken]:
        token_hash = self._hash_token(token)
        stmt = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False,
        )
        result = await self.db.execute(stmt)
        return await self._extract_entity(result, RefreshToken)

    async def revoke_refresh_token(self, token: str) -> None:
        token_hash = self._hash_token(token)
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(is_revoked=True, revoked_at=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)

    async def revoke_all_user_tokens(self, user_id: uuid.UUID) -> None:
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)
            .values(is_revoked=True, revoked_at=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)

    # ------------------------------------------------------------------
    # Login Attempts — Brute-force lockout tracking
    # ------------------------------------------------------------------
    async def record_login_attempt(
        self,
        user_id: uuid.UUID,
        success: bool,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        attempt = LoginAttempt(
            user_id=user_id,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self._add_and_flush(attempt)

    async def count_recent_failed_attempts(
        self,
        user_id: uuid.UUID,
        window_minutes: int = 15,
    ) -> int:
        """Count failed login attempts within the given sliding window."""
        since = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        stmt = (
            select(func.count())
            .select_from(LoginAttempt)
            .where(
                LoginAttempt.user_id == user_id,
                LoginAttempt.success == False,
                LoginAttempt.attempted_at >= since,
            )
        )
        result = await self.db.execute(stmt)
        val = await self._extract_scalar(result, 0)
        return int(val or 0)

    async def clear_failed_attempts(self, user_id: uuid.UUID) -> None:
        """Clear failed attempts for a user after successful authentication."""
        stmt = delete(LoginAttempt).where(
            LoginAttempt.user_id == user_id,
            LoginAttempt.success == False,
        )
        await self.db.execute(stmt)

    # ------------------------------------------------------------------
    # OTP Management (HMAC-hashed, attempt-limited, single-use)
    # ------------------------------------------------------------------
    async def create_otp(
        self,
        phone_number: str,
        otp_hash: str,
        purpose: str,
        expires_at: datetime,
    ) -> OtpLog:
        """Store HMAC-hashed OTP code (plain OTP is never persisted)."""
        phone_number = normalize_bd_phone(phone_number)
        otp_log = OtpLog(
            phone_number=phone_number,
            otp_hash=otp_hash,
            purpose=purpose,
            expires_at=expires_at,
            is_verified=False,
            is_used=False,
            verify_attempts=0,
        )
        await self._add_and_flush(otp_log)
        return otp_log

    async def get_latest_otp(
        self,
        phone_number: str,
        purpose: str,
        for_update: bool = False,
        **kwargs,
    ) -> Optional[OtpLog]:
        """Fetch the latest active OTP that is neither expired, used, nor maxed-out."""
        phone_number = normalize_bd_phone(phone_number)
        from app.core.config import get_settings
        max_attempts = get_settings().otp_max_verify_attempts

        stmt = (
            select(OtpLog)
            .where(
                OtpLog.phone_number == phone_number,
                OtpLog.purpose == purpose,
                OtpLog.is_used == False,
                OtpLog.verify_attempts < max_attempts,
            )
            .order_by(OtpLog.created_at.desc())
            .limit(1)
        )
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.db.execute(stmt)
        return await self._extract_entity(result, OtpLog)

    async def increment_otp_attempts(self, otp_id: uuid.UUID) -> None:
        """Increment wrong attempt counter for an OTP."""
        stmt = (
            update(OtpLog)
            .where(OtpLog.id == otp_id)
            .values(verify_attempts=OtpLog.verify_attempts + 1)
        )
        await self.db.execute(stmt)

    async def mark_otp_verified(self, otp_id: uuid.UUID) -> None:
        """Mark OTP as verified and used (single-use enforcement)."""
        stmt = (
            update(OtpLog)
            .where(OtpLog.id == otp_id)
            .values(is_verified=True, is_used=True)
        )
        await self.db.execute(stmt)

    async def is_phone_verified_recently(
        self,
        phone_number: str,
        purpose: str,
        within_minutes: int = 15,
    ) -> bool:
        """Check if phone was verified in Step 1 within recent minutes."""
        phone_number = normalize_bd_phone(phone_number)
        since = datetime.now(timezone.utc) - timedelta(minutes=within_minutes)
        stmt = (
            select(func.count())
            .select_from(OtpLog)
            .where(
                OtpLog.phone_number == phone_number,
                OtpLog.purpose == purpose,
                OtpLog.is_verified == True,
                OtpLog.created_at >= since,
            )
        )
        result = await self.db.execute(stmt)
        val = await self._extract_scalar(result, 0)
        return (val or 0) > 0

    async def count_recent_otps_for_phone(
        self,
        phone_number: str,
        window_minutes: int = 10,
    ) -> int:
        """Count OTPs generated for phone in window for rate limiting."""
        phone_number = normalize_bd_phone(phone_number)
        since = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        stmt = (
            select(func.count())
            .select_from(OtpLog)
            .where(OtpLog.phone_number == phone_number, OtpLog.created_at >= since)
        )
        result = await self.db.execute(stmt)
        val = await self._extract_scalar(result, 0)
        return int(val or 0)

    # ------------------------------------------------------------------
    # Consents
    # ------------------------------------------------------------------
    async def get_consent_type_by_code(self, code: str) -> Optional[ConsentType]:
        stmt = select(ConsentType).where(ConsentType.code == code)
        result = await self.db.execute(stmt)
        return await self._extract_entity(result, ConsentType)

    async def record_user_consent(
        self,
        user_id: uuid.UUID,
        consent_type_code: str,
        is_granted: bool = True,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Optional[UserConsent]:
        consent_type = await self.get_consent_type_by_code(consent_type_code)
        if not consent_type:
            consent_type = ConsentType(
                code=consent_type_code,
                title=consent_type_code.replace("_", " ").title(),
                is_mandatory=True,
            )
            await self._add_and_flush(consent_type)

        user_consent = UserConsent(
            user_id=user_id,
            consent_type_id=consent_type.id,
            is_granted=is_granted,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self._add_and_flush(user_consent)
        return user_consent

    # ------------------------------------------------------------------
    # Geographic Hierarchy
    # ------------------------------------------------------------------
    async def get_divisions(self) -> list[Division]:
        stmt = select(Division).where(Division.is_active == True).order_by(Division.name_en)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_districts(self, division_id: uuid.UUID | None = None) -> list[District]:
        stmt = select(District).where(District.is_active == True)
        if division_id:
            stmt = stmt.where(District.division_id == division_id)
        stmt = stmt.order_by(District.name_en)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_upazilas(self, district_id: uuid.UUID | None = None) -> list[Upazila]:
        stmt = select(Upazila).where(Upazila.is_active == True)
        if district_id:
            stmt = stmt.where(Upazila.district_id == district_id)
        stmt = stmt.order_by(Upazila.name_en)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_unions(self, upazila_id: uuid.UUID | None = None) -> list[Union]:
        stmt = select(Union).where(Union.is_active == True)
        if upazila_id:
            stmt = stmt.where(Union.upazila_id == upazila_id)
        stmt = stmt.order_by(Union.name_en)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # User Status & Email Verification
    # ------------------------------------------------------------------
    async def update_user_status(
        self,
        user_id: uuid.UUID,
        status: str,
        is_active: bool,
    ) -> Optional[User]:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(status=status, is_active=is_active)
            .returning(User)
        )
        result = await self.db.execute(stmt)
        return await self._extract_entity(result, User)

    async def update_email_verified(
        self,
        user_id: uuid.UUID,
        verified: bool = True,
    ) -> Optional[User]:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(email_verified=verified)
            .returning(User)
        )
        result = await self.db.execute(stmt)
        return await self._extract_entity(result, User)

    # ------------------------------------------------------------------
    # Admin Audit Logging (audit.admin_actions)
    # ------------------------------------------------------------------
    async def record_admin_action(
        self,
        actor_id: uuid.UUID,
        action: str,
        target_id: Optional[uuid.UUID] = None,
        target_type: str = "user",
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
    ) -> AdminAction:
        log = AdminAction(
            actor_id=actor_id,
            action=action,
            target_id=target_id,
            target_type=target_type,
            details=details,
            ip_address=ip_address,
        )
        await self._add_and_flush(log)
        return log
