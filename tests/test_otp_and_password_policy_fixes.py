# ============================================================================
# KrishiBondhu Bangladesh — Tests for Farmer Password Policy & OTP Lockout/Rate Limit
# ============================================================================

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.core.config import settings
from app.core.exceptions import InvalidOtpError
from app.core.security import hmac_hash_otp
from app.schemas.auth import (
    FarmerAgentRegisterRequest,
    RegisterRequest,
    ResetPasswordRequest,
    validate_farmer_pin,
    validate_strong_password,
)
from app.services.auth import AuthService
from app.services.otp_service import OtpService, phone_rate_limiter


# ── Bug 6: Farmer Password Policy Unification ────────────────────────────────

class TestFarmerPasswordPolicyUnification:
    """Verifies that farmer registration and password reset use the unified policy:
    - Min 6 characters/digits
    - Accepts numeric PIN (e.g. 123456)
    - Accepts alphanumeric password (e.g. Farmer@12345)
    - Rejects anything less than 6 characters
    - Privileged roles require strong password (min 8, uppercase, lowercase, digit)
    """

    def test_validate_farmer_pin_accepts_pin_and_alphanumeric(self):
        # 6-digit numeric PIN
        assert validate_farmer_pin("123456") == "123456"
        # Alphanumeric password
        assert validate_farmer_pin("Farmer@12345") == "Farmer@12345"
        # Short password/PIN (< 6) raises ValueError
        with pytest.raises(ValueError) as exc:
            validate_farmer_pin("12345")
        assert "at least 6" in str(exc.value)

    def test_register_request_farmer_allows_both_pin_and_password(self):
        # Numeric PIN
        req_pin = RegisterRequest(
            phone_number="01712345678",
            password="123456",
            full_name="Farmer Rahim",
            role_code="farmer",
        )
        assert req_pin.password == "123456"

        # Alphanumeric password
        req_alpha = RegisterRequest(
            phone_number="01712345678",
            password="Farmer@12345",
            full_name="Farmer Rahim",
            role_code="farmer",
        )
        assert req_alpha.password == "Farmer@12345"

        # Short password (< 6) fails
        with pytest.raises(ValidationError):
            RegisterRequest(
                phone_number="01712345678",
                password="12345",
                full_name="Farmer Rahim",
                role_code="farmer",
            )

    def test_multi_step_farmer_register_request_allows_both_pin_and_password(self):
        req_pin = FarmerAgentRegisterRequest(
            phone_number="01712345678",
            password="123456",
            full_name="Farmer Karim",
            role="farmer",
            terms_accepted=True,
        )
        assert req_pin.password == "123456"

        req_alpha = FarmerAgentRegisterRequest(
            phone_number="01712345678",
            password="FarmerPass@123",
            full_name="Farmer Karim",
            role="farmer",
            terms_accepted=True,
        )
        assert req_alpha.password == "FarmerPass@123"

    def test_privileged_roles_require_strong_password_in_registration(self):
        # Agent role requires uppercase, lowercase, digit, min 8
        with pytest.raises(ValueError):
            FarmerAgentRegisterRequest(
                phone_number="01712345678",
                password="weak",
                full_name="Agent Salam",
                role="agent",
                terms_accepted=True,
            )

        agent_valid = FarmerAgentRegisterRequest(
            phone_number="01712345678",
            password="StrongAgentPass1!",
            full_name="Agent Salam",
            role="agent",
            terms_accepted=True,
        )
        assert agent_valid.password == "StrongAgentPass1!"

    @pytest.mark.asyncio
    async def test_reset_password_farmer_accepts_both_pin_and_alphanumeric(self):
        mock_db = AsyncMock()
        service = AuthService(mock_db)

        phone = "01712345678"
        sb_user = {"id": str(uuid.uuid4()), "phone_number": phone, "role_code": "farmer"}

        with patch("app.services.auth.supabase_client.get_user_by_phone", new_callable=AsyncMock) as mock_sb, \
             patch.object(service.repo, "get_user_by_phone", new_callable=AsyncMock) as mock_local, \
             patch.object(service.otp_service, "verify_otp", new_callable=AsyncMock), \
             patch("app.services.auth.supabase_client.update_user_password", new_callable=AsyncMock):

            mock_sb.return_value = sb_user
            mock_local.return_value = None

            # 1. Reset with 6-digit numeric PIN succeeds
            payload_pin = ResetPasswordRequest(
                phone_number=phone,
                otp_code="123456",
                new_password="654321",
            )
            await service.reset_password(payload_pin)

            # 2. Reset with alphanumeric password succeeds
            payload_alpha = ResetPasswordRequest(
                phone_number=phone,
                otp_code="123456",
                new_password="NewFarmerPass@2026",
            )
            await service.reset_password(payload_alpha)

            # 3. Reset with short password fails validation
            with pytest.raises(ValidationError):
                ResetPasswordRequest(
                    phone_number=phone,
                    otp_code="123456",
                    new_password="12345",
                )


# ── Bugs 1, 2, 3: OTP Invalidation, Lockout & Generation Rate Limit ─────────

class TestOtpStrictLockoutAndRateLimiting:
    @pytest.mark.asyncio
    async def test_strict_lockout_blocks_correct_otp_after_five_attempts(self):
        """Once OTP reaches 5 failed attempts, even entering the CORRECT OTP
        on attempt 6+ returns 400 (InvalidOtpError) with 'নতুন OTP চান' and never 200.
        """
        mock_db = AsyncMock()
        service = OtpService(mock_db)

        valid_otp = "852963"
        otp_hash = hmac_hash_otp(valid_otp, settings.otp_hmac_secret)

        class MockOtpRecord:
            def __init__(self):
                self.id = uuid.uuid4()
                self.otp_hash = otp_hash
                self.expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
                self.is_used = False
                self.verify_attempts = 0

        record = MockOtpRecord()
        service.repo.get_latest_otp = AsyncMock(return_value=record)
        service.repo.increment_otp_attempts = AsyncMock()
        service.repo.mark_otp_consumed = AsyncMock()

        # Attempts 1 to 4: Wrong OTP
        for attempt in range(4):
            record.verify_attempts = attempt
            with pytest.raises(InvalidOtpError) as exc_info:
                await service.verify_otp("01712000001", "000000", purpose="registration")
            assert "attempt(s) remaining" in str(exc_info.value.detail)
            assert exc_info.value.status_code == 400

        # Attempt 5: Final wrong attempt -> Burns OTP and raises invalidation error
        record.verify_attempts = 4
        with pytest.raises(InvalidOtpError) as exc_info:
            await service.verify_otp("01712000001", "000000", purpose="registration")
        assert "invalidated" in str(exc_info.value.detail)
        assert "নতুন OTP চান" in str(exc_info.value.detail)
        assert exc_info.value.status_code == 400
        assert service.repo.mark_otp_consumed.called

        # Attempt 6+: Correct OTP entered after 5 failures -> MUST FAIL with 400
        record.verify_attempts = 5
        with pytest.raises(InvalidOtpError) as exc_info:
            await service.verify_otp("01712000001", valid_otp, purpose="registration")
        assert "invalidated" in str(exc_info.value.detail)
        assert "নতুন OTP চান" in str(exc_info.value.detail)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_otp_generation_rate_limit_across_purposes(self):
        """OTP generation rate limit limits to max 5 requests per hour
        across login, registration, and password reset.
        """
        mock_db = AsyncMock()
        service = OtpService(mock_db)

        test_phone = "+8801700998877"
        phone_rate_limiter._store.pop(test_phone, None)

        service.repo.create_otp = AsyncMock()

        # Simulate 5 OTP requests across different purposes:
        purposes = ["registration", "login", "reset_password", "registration", "login"]
        for idx, purpose in enumerate(purposes):
            service.repo.count_recent_otps_for_phone = AsyncMock(return_value=idx)
            res = await service.send_otp(phone_number=test_phone, purpose=purpose)
            assert res["phone_number"] == test_phone

        # 6th request within the hour should be blocked with 429
        service.repo.count_recent_otps_for_phone = AsyncMock(return_value=5)
        with pytest.raises(HTTPException) as exc_info:
            await service.send_otp(phone_number=test_phone, purpose="reset_password")
        assert exc_info.value.status_code == 429
        assert "Too many OTP requests" in str(exc_info.value.detail)
        assert "নতুন OTP চান" in str(exc_info.value.detail) or "সীমা অতিক্রম" in str(exc_info.value.detail)
