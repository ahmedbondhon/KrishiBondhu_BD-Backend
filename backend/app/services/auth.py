# ============================================================================
# KrishiBondhu Bangladesh — Auth Service
# Complete business logic for multi-step registration, OTP login,
# password reset, password/PIN authentication, and consent tracking
# ============================================================================

# ============================================================================
# KrishiBondhu Bangladesh — Auth Service (Minimal & Unified)
# ============================================================================

from datetime import datetime, timedelta, timezone
import logging
import uuid

from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import (
    AccountLockedError,
    AccountNotActiveError,
    AuthenticationError,
    ConsentRequiredError,
    DuplicateUserError,
    InvalidRefreshTokenError,
    PermissionDeniedError,
    PhoneNotVerifiedError,
    RoleNotFoundError,
    UserNotFoundError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token_safe,
    hash_password,
    normalize_bd_phone,
    verify_password,
)
from app.models.auth import User
from app.models.geo import District, Union, Upazila
from app.repositories.auth import AuthRepository
from app.schemas.auth import (
    AdminCreateUserRequest,
    ExpertRegisterRequest,
    FarmerAgentRegisterRequest,
    LoginRequest,
    ResetPasswordRequest,
    SupportContactResponse,
    TokenResponse,
    UserResponse,
    validate_farmer_pin,
    validate_strong_password,
)
from app.services.otp_service import OtpService
from app.services.supabase_client import supabase_client

logger = logging.getLogger(__name__)
settings = get_settings()


class AuthService:
    """Orchestrates authentication, OTP, registration, and user profiles."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AuthRepository(db)
        self.otp_service = OtpService(db)

    # ------------------------------------------------------------------
    # Shared Registration Core (Eliminates Farmer/Agent vs Expert duplication)
    # ------------------------------------------------------------------
    async def _register_user(
        self,
        payload: FarmerAgentRegisterRequest | ExpertRegisterRequest,
        role_code: str,
        status: str,
        is_active: bool,
        ip_address: str | None,
        user_agent: str | None,
    ) -> User:
        phone = normalize_bd_phone(payload.phone_number)
        payload.phone_number = phone

        # 1. Duplicate check
        if await supabase_client.get_user_by_phone(phone) or await self.repo.phone_exists(phone):
            raise DuplicateUserError("phone_number")
        if payload.email and (await supabase_client.get_user_by_email(payload.email) or await self.repo.email_exists(payload.email)):
            raise DuplicateUserError("email")

        # 2. Verify Phone & Consents
        if not await self.otp_service.is_verified(phone, "registration", payload.otp_code, payload.verification_token):
            raise PhoneNotVerifiedError("Phone verification required. Please verify OTP in Step 1.")
        if getattr(payload, "verification_token", None):
            self.otp_service.consume_verification_token(payload.verification_token)
        if not payload.terms_accepted:
            raise ConsentRequiredError("You must agree to the Terms of Service to register.")
        if not payload.privacy_accepted:
            raise ConsentRequiredError("You must agree to the Privacy Policy to register.")

        # 3. Resolve Role & Geo Hierarchy
        role = await self.repo.get_role_by_code(role_code)
        if not role:
            raise RoleNotFoundError(role_code)

        div_id, dist_id, upa_id, uni_id = await self._resolve_geo_ids(
            getattr(payload, "division_id", None),
            getattr(payload, "district_id", None),
            getattr(payload, "upazila_id", None),
            getattr(payload, "union_id", None),
        )

        # 4. Create Local User
        user = await self.repo.create_user(User(
            full_name=payload.full_name,
            phone_number=phone,
            password_hash=hash_password(payload.password),
            email=payload.email,
            role_id=role.id,
            division_id=div_id,
            district_id=dist_id,
            upazila_id=upa_id,
            union_id=uni_id,
            village=getattr(payload, "village", None),
            preferred_language=payload.preferred_language,
            preferred_communication=getattr(payload, "preferred_communication", "sms") or "sms",
            avatar_url=getattr(payload, "avatar_url", None),
            status=status,
            is_active=is_active,
            phone_verified=True,
        ))

        # 5. Record Consents & Sync to Supabase
        loc_granted = bool(payload.location_permission_granted)
        for code, granted in [("terms_of_service", True), ("privacy_policy", True), ("location_data", loc_granted)]:
            await self.repo.record_user_consent(
                user_id=user.id,
                consent_type_code=code,
                is_granted=granted,
                ip_address=ip_address,
                user_agent=user_agent,
            )

        await self._sync_user_to_supabase(
            user=user,
            role_code=role_code,
            status=status,
            is_active=is_active,
            location_permission_granted=loc_granted,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return user

    async def _resolve_geo_ids(
        self, div_id: uuid.UUID | None, dist_id: uuid.UUID | None, upa_id: uuid.UUID | None, uni_id: uuid.UUID | None
    ) -> tuple[uuid.UUID | None, uuid.UUID | None, uuid.UUID | None, uuid.UUID | None]:
        if uni_id and not upa_id and (un := await self.db.get(Union, uni_id)):
            upa_id = un.upazila_id
        if upa_id and not dist_id and (upa := await self.db.get(Upazila, upa_id)):
            dist_id = upa.district_id
        if dist_id and not div_id and (dist := await self.db.get(District, dist_id)):
            div_id = dist.division_id
        return div_id, dist_id, upa_id, uni_id

    async def register_farmer_agent(
        self, payload: FarmerAgentRegisterRequest, ip_address: str | None = None, user_agent: str | None = None
    ) -> tuple[User, TokenResponse]:
        user = await self._register_user(payload, payload.role, "active", True, ip_address, user_agent)
        return user, await self._issue_tokens(user, remember_me=False)

    async def register_expert(
        self, payload: ExpertRegisterRequest, ip_address: str | None = None, user_agent: str | None = None
    ) -> tuple[User, None]:
        user = await self._register_user(payload, "expert", "pending_approval", False, ip_address, user_agent)
        return user, None

    async def create_admin_user(self, payload: AdminCreateUserRequest, created_by: User) -> tuple[User, str]:
        if created_by.role_code not in ("administrator", "technical_admin", "admin"):
            raise PermissionDeniedError("Only admins can create admin accounts.")

        payload.phone_number = normalize_bd_phone(payload.phone_number)
        if await self.repo.phone_exists(payload.phone_number):
            raise DuplicateUserError("phone_number")
        if await self.repo.email_exists(payload.email):
            raise DuplicateUserError("email")

        role = await self.repo.get_role_by_code(payload.role)
        if not role and payload.role in ("admin", "administrator"):
            role = await self.repo.get_role_by_code("admin" if payload.role == "administrator" else "administrator")
        if not role:
            raise RoleNotFoundError(payload.role)

        user = await self.repo.create_user(User(
            full_name=payload.full_name,
            phone_number=payload.phone_number,
            password_hash=hash_password(payload.password),
            email=payload.email,
            role_id=role.id,
            status="active",
            is_active=True,
            phone_verified=True,
        ))
        return user, role.code

    # ------------------------------------------------------------------
    # Unified Admin Approval / Rejection
    # ------------------------------------------------------------------
    async def _set_user_approval(
        self, user_id: uuid.UUID, admin_user: User, new_status: str, action: str, reason: str | None = None, ip: str | None = None
    ) -> User:
        user = await self.repo.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError("id")

        is_active = new_status == "active"
        updated = await self.repo.update_user_status(user_id, status=new_status, is_active=is_active)
        details = {"previous_status": user.status, "new_status": new_status}
        if reason is not None:
            details["reason"] = reason

        await self.repo.record_admin_action(
            actor_id=admin_user.id,
            action=action,
            target_id=user_id,
            target_type="user",
            details=details,
            ip_address=ip,
        )
        await supabase_client.update_user_status(str(user_id), new_status)
        return updated or user

    async def approve_user(self, user_id: uuid.UUID, admin_user: User, ip_address: str | None = None) -> User:
        return await self._set_user_approval(user_id, admin_user, "active", "approve_user", ip=ip_address)

    async def reject_user(self, user_id: uuid.UUID, admin_user: User, reason: str | None = None, ip_address: str | None = None) -> User:
        return await self._set_user_approval(user_id, admin_user, "rejected", "reject_user", reason=reason, ip=ip_address)

    # ------------------------------------------------------------------
    # Email Verification
    # ------------------------------------------------------------------
    def generate_email_verification_token(self, user_id: uuid.UUID, email: str) -> str:
        now = datetime.now(timezone.utc)
        return jwt.encode(
            {"sub": str(user_id), "email": email, "type": "email_verification", "iat": now, "exp": now + timedelta(hours=24)},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

    async def verify_email_token(self, token: str) -> User:
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            if payload.get("type") != "email_verification":
                raise ValueError()
            user_id = uuid.UUID(payload["sub"])
        except (JWTError, KeyError, ValueError):
            raise AuthenticationError("Email verification link is invalid or expired.")

        user = await self.repo.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundError("id")

        updated = await self.repo.update_email_verified(user_id, verified=True)
        await supabase_client.update_user_email_verified(str(user_id), True)
        return updated or user

    # ------------------------------------------------------------------
    # Unified Login & OTP Login Helpers
    # ------------------------------------------------------------------
    async def _complete_supabase_login(
        self, sb_user: dict, remember_me: bool, ip: str | None, ua: str | None
    ) -> TokenResponse:
        status = sb_user.get("status", "active")
        if status != "active" or not sb_user.get("is_active", True):
            raise AccountNotActiveError(status)
        await supabase_client.update_last_login(sb_user["id"])
        await supabase_client.record_login_attempt(sb_user["id"], ip, ua, True)
        return self._build_supabase_token_response(sb_user, status, remember_me)

    async def _complete_local_login(
        self, user: User, remember_me: bool, ip: str | None, ua: str | None
    ) -> TokenResponse:
        if user.effective_status != "active":
            raise AccountNotActiveError(user.effective_status)
        await self.repo.clear_failed_attempts(user.id)
        await self.repo.record_login_attempt(user_id=user.id, success=True, ip_address=ip, user_agent=ua)
        await self.repo.update_last_login(user.id)
        return await self._issue_tokens(user, remember_me=remember_me)

    async def login(self, payload: LoginRequest, ip_address: str | None = None, user_agent: str | None = None) -> TokenResponse:
        if payload.phone_number:
            payload.phone_number = normalize_bd_phone(payload.phone_number)
            sb_user = await supabase_client.get_user_by_phone(payload.phone_number)
        else:
            sb_user = await supabase_client.get_user_by_email(payload.email) if payload.email else None

        # 1. Supabase Login
        if sb_user:
            valid_pw = bool(sb_user.get("password_hash") and verify_password(payload.password, sb_user["password_hash"]))
            if not valid_pw and settings.enable_supabase_auth_fallback:
                local_u = await self.repo.get_user_by_phone(sb_user["phone_number"])
                if local_u and local_u.effective_status == "active" and local_u.password_hash and verify_password(payload.password, local_u.password_hash):
                    valid_pw = True
                    await supabase_client.update_user_password(sb_user["phone_number"], local_u.password_hash)

            if not valid_pw:
                await supabase_client.record_login_attempt(sb_user["id"], ip_address, user_agent, False)
                raise AuthenticationError("Invalid phone number, email, or password/PIN.")

            return await self._complete_supabase_login(sb_user, payload.remember_me, ip_address, user_agent)

        # 2. Local DB Fallback
        user = (
            await self.repo.get_user_by_phone(payload.phone_number)
            if payload.phone_number
            else await self.repo.get_user_by_email(payload.email)
        )
        if not user:
            raise AuthenticationError("Invalid phone number, email, or password/PIN.")

        failed_count = await self.repo.count_recent_failed_attempts(user.id, window_minutes=settings.login_lockout_minutes)
        if failed_count >= settings.max_login_attempts:
            raise AccountLockedError(settings.login_lockout_minutes)

        if not user.password_hash or not verify_password(payload.password, user.password_hash):
            await self.repo.record_login_attempt(user_id=user.id, success=False, ip_address=ip_address, user_agent=user_agent)
            if settings.max_login_attempts - (failed_count + 1) <= 0:
                raise AccountLockedError(settings.login_lockout_minutes)
            raise AuthenticationError("Invalid phone number, email, or password/PIN.")

        return await self._complete_local_login(user, payload.remember_me, ip_address, user_agent)

    async def request_otp_login(self, phone_number: str) -> dict:
        phone = normalize_bd_phone(phone_number)
        sb_user = await supabase_client.get_user_by_phone(phone)
        user = await self.repo.get_user_by_phone(phone)

        is_active = (
            (sb_user and sb_user.get("status") == "active" and sb_user.get("is_active", True))
            or (not sb_user and user and user.effective_status == "active")
        )
        if is_active:
            return await self.otp_service.send_otp(phone_number=phone_number, purpose="login")
        return self._generic_otp_response(phone_number, "login")

    async def verify_otp_login(
        self, phone_number: str, otp_code: str, remember_me: bool = False, ip_address: str | None = None, user_agent: str | None = None
    ) -> TokenResponse:
        phone = normalize_bd_phone(phone_number)
        await self.otp_service.verify_otp(phone_number=phone, otp_code=otp_code, purpose="login")

        if sb_user := await supabase_client.get_user_by_phone(phone):
            return await self._complete_supabase_login(sb_user, remember_me, ip_address, user_agent)

        user = await self.repo.get_user_by_phone(phone)
        if not user:
            raise UserNotFoundError("phone number")
        return await self._complete_local_login(user, remember_me, ip_address, user_agent)

    # ------------------------------------------------------------------
    # Password Reset
    # ------------------------------------------------------------------
    async def forgot_password_request(self, phone_number: str) -> dict:
        phone = normalize_bd_phone(phone_number)
        if await supabase_client.get_user_by_phone(phone) or await self.repo.get_user_by_phone(phone):
            return await self.otp_service.send_otp(phone_number=phone_number, purpose="reset_password")
        return self._generic_otp_response(phone_number, "reset_password")

    async def reset_password(self, payload: ResetPasswordRequest) -> None:
        phone = normalize_bd_phone(payload.phone_number)
        sb_user = await supabase_client.get_user_by_phone(phone)
        user = await self.repo.get_user_by_phone(phone)
        if not sb_user and not user:
            raise UserNotFoundError("phone number")

        # Determine user role and validate password policy
        role_code = "farmer"
        if user and user.role:
            role_code = user.role.code
        elif user and hasattr(user, "role_code"):
            role_code = user.role_code
        elif sb_user and isinstance(sb_user, dict):
            role_code = sb_user.get("role_code") or (sb_user.get("roles") or {}).get("code") or "farmer"
        elif sb_user and hasattr(sb_user, "role_code"):
            role_code = sb_user.role_code

        try:
            if role_code == "farmer":
                validate_farmer_pin(payload.new_password)
            else:
                validate_strong_password(payload.new_password, role_code.capitalize())
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e),
            )

        if payload.verification_token:
            if not self.otp_service.decode_verification_token(payload.verification_token, phone, "reset_password"):
                raise AuthenticationError("Invalid or expired reset token.")
            self.otp_service.consume_verification_token(payload.verification_token)
        elif payload.otp_code:
            await self.otp_service.verify_otp(phone_number=phone, otp_code=payload.otp_code, purpose="reset_password")
        else:
            raise AuthenticationError("Either otp_code or verification_token is required.")

        new_hash = hash_password(payload.new_password)
        await supabase_client.update_user_password(phone, new_hash)
        if user:
            await self.repo.update_user_password(user.id, new_hash)
            await self.repo.revoke_all_user_tokens(user.id)

    # ------------------------------------------------------------------
    # Profile & Tokens
    # ------------------------------------------------------------------
    async def update_language(self, user_id: uuid.UUID, language: str) -> User:
        await self.repo.update_user_language(user_id, language)
        return await self.repo.get_user_by_id(user_id)

    async def get_support_contact(self) -> SupportContactResponse:
        return SupportContactResponse(
            helpline_number=settings.support_helpline,
            support_phone=settings.support_phone,
            support_email=settings.support_email,
            available_hours_bn=settings.support_available_hours_bn,
            available_hours_en=settings.support_available_hours_en,
        )

    async def refresh_tokens(self, refresh_token_str: str) -> TokenResponse:
        claims = decode_token_safe(refresh_token_str)
        stored = await self.repo.get_refresh_token(refresh_token_str) if claims and claims.get("type") == "refresh" else None
        if not stored:
            raise InvalidRefreshTokenError()

        await self.repo.revoke_refresh_token(refresh_token_str)
        if stored.expires_at < datetime.now(timezone.utc):
            raise InvalidRefreshTokenError()

        user = await self.repo.get_user_by_id(stored.user_id)
        if not user or user.effective_status != "active":
            raise AuthenticationError("Account is no longer active.")
        return await self._issue_tokens(user, remember_me=False)

    async def logout(self, refresh_token_str: str) -> None:
        await self.repo.revoke_refresh_token(refresh_token_str)

    async def logout_all(self, user_id: uuid.UUID) -> None:
        await self.repo.revoke_all_user_tokens(user_id)

    async def get_current_user(self, user_id: uuid.UUID) -> User | None:
        return await self.repo.get_user_by_id(user_id)

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _generic_otp_response(phone: str, purpose: str) -> dict:
        return {
            "message": f"OTP sent to {phone} successfully.",
            "phone_number": phone,
            "purpose": purpose,
            "expires_in_seconds": settings.otp_expire_minutes * 60,
            "resend_after": 60,
        }

    async def _sync_user_to_supabase(
        self,
        user: User,
        role_code: str = "farmer",
        status: str = "active",
        is_active: bool = True,
        loc_granted: bool = False,
        ip: str | None = None,
        ua: str | None = None,
        location_permission_granted: bool | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        if location_permission_granted is not None:
            loc_granted = location_permission_granted
        if ip_address is not None:
            ip = ip_address
        if user_agent is not None:
            ua = user_agent
        default_role = "11000000-0000-0000-0000-000000000002" if role_code == "expert" else "11000000-0000-0000-0000-000000000001"
        sb_payload = {
            "id": str(user.id),
            "phone_number": user.phone_number,
            "password_hash": user.password_hash,
            "full_name": user.full_name,
            "email": user.email,
            "role_id": await supabase_client.get_role_id_by_code(role_code) or default_role,
            "division_id": str(user.division_id) if user.division_id else None,
            "district_id": str(user.district_id) if user.district_id else None,
            "upazila_id": str(user.upazila_id) if user.upazila_id else None,
            "union_id": str(user.union_id) if user.union_id else None,
            "status": status,
            "phone_verified": True,
            "email_verified": False,
            "preferred_language": user.preferred_language,
            "is_active": is_active,
            "is_deleted": False,
        }
        if not await supabase_client.create_user(sb_payload) and (user.division_id or user.district_id):
            for k in ("division_id", "district_id", "upazila_id", "union_id"):
                sb_payload[k] = None
            await supabase_client.create_user(sb_payload)

        for code, granted in [("terms_of_service", True), ("privacy_policy", True), ("location_data", loc_granted)]:
            await supabase_client.record_user_consent(str(user.id), code, ip, ua, is_granted=granted)

    def _build_token_pair(self, user_id: uuid.UUID, role: str, status: str, remember_me: bool) -> tuple[str, str, datetime]:
        access_token = create_access_token(user_id=user_id, role_code=role, role=role, status=status)
        days = settings.remember_me_refresh_token_expire_days if remember_me else settings.refresh_token_expire_days
        refresh_token, refresh_expires = create_refresh_token(user_id=user_id, expires_delta=timedelta(days=days))
        return access_token, refresh_token, refresh_expires

    def _build_supabase_token_response(self, sb_user: dict, status: str, remember_me: bool) -> TokenResponse:
        role_code = sb_user.get("role_code", "farmer")
        u_id = uuid.UUID(sb_user["id"])
        access_token, refresh_token, _ = self._build_token_pair(u_id, role_code, status, remember_me)

        created_at = datetime.now(timezone.utc)
        if sb_user.get("created_at"):
            try:
                created_at = datetime.fromisoformat(sb_user["created_at"].replace("Z", "+00:00"))
            except ValueError:
                pass

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=UserResponse(
                id=u_id,
                phone_number=sb_user["phone_number"],
                full_name=sb_user["full_name"],
                email=sb_user.get("email"),
                role=role_code,
                status=status,
                preferred_language=sb_user.get("preferred_language", "bn"),
                preferred_communication=sb_user.get("preferred_communication") or "sms",
                avatar_url=sb_user.get("avatar_url"),
                phone_verified=sb_user.get("phone_verified", True),
                email_verified=sb_user.get("email_verified", False),
                last_login_at=datetime.now(timezone.utc),
                created_at=created_at,
            ),
        )

    async def _issue_tokens(self, user: User, remember_me: bool = False) -> TokenResponse:
        access_token, refresh_token, refresh_expires = self._build_token_pair(
            user.id, user.role_code, user.effective_status, remember_me
        )
        await self.repo.store_refresh_token(user_id=user.id, token=refresh_token, expires_at=refresh_expires)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=_user_to_response(user),
        )


def _user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        full_name=user.full_name,
        phone_number=user.phone_number,
        email=user.email,
        role=user.role_code,
        status=user.effective_status,
        preferred_language=user.preferred_language,
        preferred_communication=getattr(user, "preferred_communication", "sms") or "sms",
        avatar_url=user.avatar_url,
        division_id=user.division_id,
        district_id=user.district_id,
        upazila_id=user.upazila_id,
        union_id=user.union_id,
        village=user.village,
        phone_verified=user.phone_verified,
        email_verified=user.email_verified,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )


ExtendedAuthService = AuthService