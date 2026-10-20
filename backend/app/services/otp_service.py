# ============================================================================
# KrishiBondhu Bangladesh — OTP Service (Secure)
# HMAC-hashed storage, attempt limits, single-use, SMS simulator support
# ============================================================================

import asyncio
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import logging
import threading
import time

from fastapi import HTTPException
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import InvalidOtpError, OtpExpiredError
from app.core.security import generate_numeric_otp, hmac_hash_otp, hmac_verify_otp, normalize_bd_phone
from app.repositories.auth import AuthRepository
from app.services.supabase_client import supabase_client

logger = logging.getLogger("krishibondhu.otp")
settings = get_settings()


class SmsSimulatorInbox:
    """Thread-safe in-memory store for SMS simulator messages."""

    def __init__(self, ttl_seconds: int = 300):
        self._store: dict[str, list[dict]] = defaultdict(list)
        self._lock = threading.Lock()
        self._ttl = ttl_seconds

    def put(self, phone: str, message: str, otp_code: str = "") -> None:
        with self._lock:
            self._cleanup()
            self._store[phone].append({"message": message, "otp_code": otp_code, "created_at": time.time()})

    def get_and_delete(self, phone: str) -> list[dict]:
        with self._lock:
            self._cleanup()
            return self._store.pop(phone, [])

    def _cleanup(self) -> None:
        cutoff = time.time() - self._ttl
        for phone in list(self._store):
            self._store[phone] = [m for m in self._store[phone] if m["created_at"] > cutoff]
            if not self._store[phone]:
                del self._store[phone]


class IpRateLimiter:
    """Simple in-memory per-IP rate limiter."""

    def __init__(self):
        self._store: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def check_and_record(self, ip: str, max_count: int, window_minutes: int) -> bool:
        now, cutoff = time.time(), time.time() - (window_minutes * 60)
        with self._lock:
            self._store[ip] = [t for t in self._store[ip] if t > cutoff]
            if len(self._store[ip]) >= max_count:
                return False
            self._store[ip].append(now)
            return True


sms_inbox = SmsSimulatorInbox()
ip_rate_limiter = IpRateLimiter()


class OtpService:
    """Handles OTP generation, HMAC hashing, SMS dispatch, and verification."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AuthRepository(db)

    def _generate_verification_token(self, phone: str, purpose: str) -> str:
        phone_norm = normalize_bd_phone(phone)
        now = datetime.now(timezone.utc)
        return jwt.encode(
            {"sub": phone_norm, "phone": phone_norm, "purpose": purpose, "type": "phone_verification", "iat": now, "exp": now + timedelta(minutes=10)},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

    def decode_verification_token(self, token: str, expected_phone: str, expected_purpose: str) -> bool:
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            return (
                (payload.get("phone") or payload.get("sub")) == normalize_bd_phone(expected_phone)
                and payload.get("purpose") == expected_purpose
                and payload.get("type") == "phone_verification"
            )
        except (JWTError, ValueError):
            return False

    def _raise_rate_limit(self, target: str) -> None:
        win = settings.otp_rate_limit_window_minutes
        raise HTTPException(
            status_code=429,
            detail=f"Too many OTP requests for this {target}. Try again after {win} minutes.",
            headers={"Retry-After": str(win * 60)},
        )

    async def send_otp(self, phone_number: str, purpose: str = "registration", ip_address: str | None = None) -> dict:
        phone = normalize_bd_phone(phone_number)
        win = settings.otp_rate_limit_window_minutes

        if await self.repo.count_recent_otps_for_phone(phone, window_minutes=win) >= settings.otp_rate_limit_per_phone:
            self._raise_rate_limit("phone")

        if ip_address and not ip_rate_limiter.check_and_record(ip_address, settings.otp_rate_limit_per_ip, win):
            self._raise_rate_limit("IP")

        otp_code = settings.otp_demo_code if settings.otp_demo_mode else generate_numeric_otp(settings.otp_length)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.otp_expire_minutes)
        otp_hash = hmac_hash_otp(otp_code, settings.otp_hmac_secret)

        await self.repo.create_otp(phone_number=phone, otp_hash=otp_hash, purpose=purpose, expires_at=expires_at)
        self._dispatch_sms(phone, otp_code, purpose)
        asyncio.create_task(supabase_client.record_otp(phone, otp_hash, expires_at))

        res = {
            "message": f"OTP sent to {phone} successfully.",
            "phone_number": phone,
            "purpose": purpose,
            "expires_in_seconds": settings.otp_expire_minutes * 60,
            "resend_after": 60,
        }
        if settings.otp_demo_mode:
            res["demo_mode"] = True
        return res

    def _dispatch_sms(self, phone: str, otp_code: str, purpose: str) -> None:
        msg = f"[কৃষিবন্ধু] আপনার ওটিপি কোড হলো: {otp_code}। মেয়াদ {settings.otp_expire_minutes} মিনিট।"
        if settings.sms_mode == "simulator":
            sms_inbox.put(phone, msg, otp_code=otp_code)
            logger.info(f"==> SMS SIMULATOR: Stored OTP for {phone} [{purpose}]")
        else:
            logger.info(f"==> SMS DISABLED: OTP for {phone} [{purpose}] | Code: {otp_code}")

    async def verify_otp(self, phone_number: str, otp_code: str, purpose: str = "registration") -> dict:
        phone = normalize_bd_phone(phone_number)
        record = await self.repo.get_latest_otp(phone_number=phone, purpose=purpose)
        if not record:
            raise InvalidOtpError("No pending OTP found for this number. Please request a new OTP.")
        if record.expires_at < datetime.now(timezone.utc):
            raise OtpExpiredError("OTP code has expired. Please request a new one.")
        if record.is_used:
            raise InvalidOtpError("This OTP has already been used. Please request a new one.")

        if not hmac_verify_otp(otp_code.strip(), record.otp_hash, settings.otp_hmac_secret):
            await self.repo.increment_otp_attempts(record.id)
            rem = settings.otp_max_verify_attempts - (record.verify_attempts + 1)
            if rem <= 0:
                raise InvalidOtpError("Too many incorrect attempts. This OTP has been invalidated. Please request a new OTP.")
            raise InvalidOtpError(f"Incorrect OTP code. {rem} attempt(s) remaining.")

        await self.repo.mark_otp_verified(record.id)
        asyncio.create_task(supabase_client.mark_otp_verified(phone, record.otp_hash))

        return {
            "message": "OTP verified successfully.",
            "phone_number": phone,
            "is_verified": True,
            "verification_token": self._generate_verification_token(phone, purpose),
        }

    async def is_verified(
        self, phone_number: str, purpose: str, otp_code: str | None = None, verification_token: str | None = None
    ) -> bool:
        phone = normalize_bd_phone(phone_number)
        if verification_token and self.decode_verification_token(verification_token, phone, purpose):
            return True
        if await self.repo.is_phone_verified_recently(phone, purpose, within_minutes=15):
            return True
        if otp_code:
            try:
                return (await self.verify_otp(phone, otp_code, purpose)).get("is_verified", False)
            except Exception:
                return False
        return False