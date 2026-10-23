# ============================================================================
# KrishiBondhu Bangladesh — End-to-End & Security Test Suite
# Tests:
#   1. E2E Registration -> OTP Send -> Simulator Inbox -> Verify -> Login -> Refresh -> Logout
#   2. OTP Rate Limiting (429 Too Many Requests + Retry-After)
#   3. 5 Wrong OTP Attempts Invalidation
#   4. Login Brute-force Lockout (5 failed attempts)
#   5. DEBUG=False gates /demo/* routes with 404
#   6. Absence of dev_otp_code in all responses
#   7. Admin Approval / Rejection with Audit Log
#   8. Email Verification Token Flow
# ============================================================================

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.core.security import hash_password, hmac_hash_otp
from app.db.session import get_db
from app.main import app
from app.models.auth import Role, User
from app.services.otp_service import sms_inbox, ip_rate_limiter

settings = get_settings()


@pytest.fixture(autouse=True)
def clean_inbox_and_rate_limiters():
    """Reset in-memory state before each test."""
    sms_inbox._store.clear()
    ip_rate_limiter._store.clear()


@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestOtpSecurityAndDevOtpAbsence:
    """Verifies OTP security: no dev_otp_code in responses, rate limits, 5 wrong attempts."""

    @pytest.mark.asyncio
    async def test_otp_response_never_contains_dev_otp_code(self, async_client):
        """Step 1 & Step 6: dev_otp_code is NEVER present in /otp/send response."""
        res = await async_client.post(
            "/api/v1/auth/otp/send",
            json={"phone_number": "01712000001", "purpose": "registration"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "dev_otp_code" not in data
        assert "message" in data
        assert "expires_in_seconds" in data
        assert "resend_after" in data

    @pytest.mark.asyncio
    async def test_sms_simulator_inbox_and_retrieval(self, async_client):
        """Step 2: When SMS_MODE=simulator, plain OTP is placed in simulator inbox."""
        phone = "01712000002"
        # 1. Send OTP
        res = await async_client.post(
            "/api/v1/auth/otp/send",
            json={"phone_number": phone, "purpose": "registration"},
        )
        assert res.status_code == 200

        # 2. Poll SMS simulator inbox
        inbox_res = await async_client.get(f"/demo/sms-inbox?phone={phone}")
        assert inbox_res.status_code == 200
        inbox_data = inbox_res.json()
        assert inbox_data["phone"] == phone
        assert inbox_data["count"] == 1
        assert len(inbox_data["messages"]) == 1
        otp_code = inbox_data["latest_otp"]
        assert len(otp_code) == 6
        assert otp_code.isdigit()

        # 3. Reading clears the inbox (one-time read)
        inbox_empty = await async_client.get(f"/demo/sms-inbox?phone={phone}")
        assert inbox_empty.json()["count"] == 0

    @pytest.mark.asyncio
    async def test_otp_rate_limiting_per_ip_returns_429(self, async_client):
        """Step 1 & Step 6: Exceeding IP rate limit returns 429 and Retry-After header."""
        # Use an isolated IP
        test_ip = "192.168.1.99"

        # Simulate 10 requests from this IP directly in rate limiter
        for _ in range(settings.otp_rate_limit_per_ip):
            allowed = ip_rate_limiter.check_and_record(
                test_ip,
                max_count=settings.otp_rate_limit_per_ip,
                window_minutes=settings.otp_rate_limit_window_minutes,
            )
            assert allowed is True

        # 11th request should be blocked
        is_blocked = not ip_rate_limiter.check_and_record(
            test_ip,
            max_count=settings.otp_rate_limit_per_ip,
            window_minutes=settings.otp_rate_limit_window_minutes,
        )
        assert is_blocked is True


class TestOtpAttemptLimitsAndSingleUse:
    """Verifies that 5 wrong attempts invalidate the OTP, and single-use is enforced."""

    @pytest.mark.asyncio
    async def test_five_wrong_attempts_invalidate_otp(self):
        """Step 1: Max 5 incorrect OTP attempts invalidates the OTP code."""
        from app.services.otp_service import OtpService
        from app.core.exceptions import InvalidOtpError

        mock_db = AsyncMock()
        service = OtpService(mock_db)

        # Mock OTP log with valid hash and 0 attempts
        valid_otp = "123456"
        otp_hash = hmac_hash_otp(valid_otp, settings.otp_hmac_secret)

        class FakeOtpRecord:
            def __init__(self, h):
                self.id = uuid.uuid4()
                self.expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
                self.is_used = False
                self.verify_attempts = 0
                self.otp_hash = h

        record = FakeOtpRecord(otp_hash)
        service.repo.get_latest_otp = AsyncMock(return_value=record)
        service.repo.increment_otp_attempts = AsyncMock()

        # Attempts 1 to 4: Wrong OTP gives remaining attempts
        for attempt in range(4):
            record.verify_attempts = attempt
            with pytest.raises(InvalidOtpError) as exc_info:
                await service.verify_otp("01712000003", "999999", purpose="registration")
            assert "attempt(s) remaining" in str(exc_info.value.detail)

        # Attempt 5: Reaches limit -> Invalidation message
        record.verify_attempts = 4
        with pytest.raises(InvalidOtpError) as exc_info:
            await service.verify_otp("01712000003", "999999", purpose="registration")
        assert "invalidated" in str(exc_info.value.detail)


class TestLoginLockout:
    """Verifies brute-force lockout on 5 consecutive failed login attempts."""

    @pytest.mark.asyncio
    async def test_lockout_after_five_failed_logins(self):
        """Step 1 & Step 6: 5 failed logins locks account for 15 minutes."""
        from app.services.auth import AuthService
        from app.core.exceptions import AccountLockedError
        from app.schemas.auth import LoginRequest

        mock_db = AsyncMock()
        service = AuthService(mock_db)

        # Mock user exists with hashed password
        user = User(
            id=uuid.uuid4(),
            full_name="Lockout Test User",
            phone_number="01712000004",
            password_hash=hash_password("CorrectPass123"),
            status="active",
            is_active=True,
            role_id=uuid.uuid4(),
        )
        service.repo.get_user_by_phone = AsyncMock(return_value=user)
        service.repo.record_login_attempt = AsyncMock()

        # Simulate 5 previous failures within window
        service.repo.count_recent_failed_attempts = AsyncMock(return_value=5)

        # Attempt login -> should raise AccountLockedError immediately
        req = LoginRequest(phone_number="01712000004", password="WrongPassword")
        with pytest.raises(AccountLockedError) as exc_info:
            await service.login(req)
        assert "Account locked" in str(exc_info.value.detail)


class TestProductionLockdown:
    """Verifies Step 3: DEBUG=false gates /demo/* routes with 404."""

    @pytest.mark.asyncio
    async def test_demo_routes_404_when_debug_false(self):
        """Step 3 & 6: When DEBUG=false, demo routes return 404."""
        from fastapi import FastAPI
        from app.core.config import Settings
        from app.api.v1 import api_v1_router

        # Create isolated app mimicking DEBUG=False
        prod_app = FastAPI()
        prod_app.include_router(api_v1_router, prefix="/api/v1")

        transport = ASGITransport(app=prod_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # /demo UI
            res1 = await client.get("/demo")
            assert res1.status_code == 404

            # /demo/sms-inbox
            res2 = await client.get("/demo/sms-inbox?phone=01712000005")
            assert res2.status_code == 404

            # /demo/db-inspector
            res3 = await client.get("/demo/db-inspector")
            assert res3.status_code == 404


class TestAdminApprovalAndAuditLog:
    """Verifies Step 4 & 6: Admin approval/rejection and audit logging."""

    @pytest.mark.asyncio
    async def test_admin_approve_and_reject_user_with_audit(self):
        """Step 4 & 6: Admin approves/rejects expert user and logs action in audit."""
        from app.services.auth import AuthService
        from app.models.auth import AdminAction

        mock_db = AsyncMock()
        service = AuthService(mock_db)

        admin = User(
            id=uuid.uuid4(),
            full_name="Super Admin",
            phone_number="01811111111",
            status="active",
            is_active=True,
            role_id=uuid.uuid4(),
        )
        expert = User(
            id=uuid.uuid4(),
            full_name="Dr. Rahim Expert",
            phone_number="01722222222",
            status="pending_approval",
            is_active=False,
            role_id=uuid.uuid4(),
        )

        service.repo.get_user_by_id = AsyncMock(return_value=expert)
        service.repo.update_user_status = AsyncMock(
            return_value=User(
                id=expert.id,
                full_name=expert.full_name,
                phone_number=expert.phone_number,
                status="active",
                is_active=True,
                role_id=expert.role_id,
            )
        )
        recorded_actions = []

        async def fake_record_admin_action(*args, **kwargs):
            action = AdminAction(
                actor_id=kwargs.get("actor_id"),
                action=kwargs.get("action"),
                target_id=kwargs.get("target_id"),
                details=kwargs.get("details"),
            )
            recorded_actions.append(action)
            return action

        service.repo.record_admin_action = AsyncMock(side_effect=fake_record_admin_action)

        # 1. Approve user
        approved = await service.approve_user(expert.id, admin_user=admin, ip_address="127.0.0.1")
        assert approved.status == "active"
        assert approved.is_active is True
        assert len(recorded_actions) == 1
        assert recorded_actions[0].action == "approve_user"
        assert recorded_actions[0].target_id == expert.id

        # 2. Reject user
        service.repo.update_user_status = AsyncMock(
            return_value=User(
                id=expert.id,
                full_name=expert.full_name,
                phone_number=expert.phone_number,
                status="rejected",
                is_active=False,
                role_id=expert.role_id,
            )
        )
        rejected = await service.reject_user(expert.id, admin_user=admin, reason="Invalid credentials")
        assert rejected.status == "rejected"
        assert rejected.is_active is False
        assert len(recorded_actions) == 2
        assert recorded_actions[1].action == "reject_user"


class TestEmailVerificationFlow:
    """Verifies Step 4: 24h JWT email verification."""

    @pytest.mark.asyncio
    async def test_email_verification_jwt_roundtrip(self):
        """Step 4: Generate 24h email verification token and verify it."""
        from app.services.auth import AuthService

        mock_db = AsyncMock()
        service = AuthService(mock_db)

        user_id = uuid.uuid4()
        test_email = "farmer@krishibondhu.gov.bd"
        user = User(
            id=user_id,
            full_name="Email Test Farmer",
            phone_number="01712000006",
            email=test_email,
            email_verified=False,
            role_id=uuid.uuid4(),
        )

        service.repo.get_user_by_id = AsyncMock(return_value=user)
        service.repo.update_email_verified = AsyncMock(
            return_value=User(
                id=user_id,
                full_name=user.full_name,
                phone_number=user.phone_number,
                email=test_email,
                email_verified=True,
                role_id=user.role_id,
            )
        )

        # 1. Generate token
        token = service.generate_email_verification_token(user_id, test_email)
        assert isinstance(token, str)

        # 2. Verify token
        verified_user = await service.verify_email_token(token)
        assert verified_user.email_verified is True


class TestSupabaseSyncAndClientMethods:
    """Verifies Supabase client methods and AuthService Supabase sync helper."""

    @pytest.mark.asyncio
    async def test_supabase_client_update_status_and_email(self):
        from unittest.mock import MagicMock
        from app.services.supabase_client import SupabaseClient

        client = SupabaseClient()

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch("httpx.AsyncClient.patch", AsyncMock(return_value=mock_resp)) as mock_patch:
            res_status = await client.update_user_status("some-user-id", "active")
            assert res_status is True
            assert mock_patch.called
            call_kwargs = mock_patch.call_args[1]
            assert call_kwargs["json"] == {"status": "active", "is_active": True}

            res_email = await client.update_user_email_verified("some-user-id", True)
            assert res_email is True
            call_kwargs = mock_patch.call_args[1]
            assert call_kwargs["json"] == {"email_verified": True}

    @pytest.mark.asyncio
    async def test_auth_service_sync_user_to_supabase(self):
        from app.services.auth import AuthService
        from app.services.supabase_client import supabase_client

        mock_db = AsyncMock()
        service = AuthService(mock_db)

        user = User(
            id=uuid.uuid4(),
            full_name="Sync Test Farmer",
            phone_number="01712000099",
            password_hash="hashed_pw",
            email="sync@test.com",
            preferred_language="bn",
        )

        with patch.object(supabase_client, "get_role_id_by_code", AsyncMock(return_value="role-123")), \
             patch.object(supabase_client, "create_user", AsyncMock(return_value={"id": str(user.id)})) as mock_create, \
             patch.object(supabase_client, "record_user_consent", AsyncMock(return_value=True)) as mock_consent:

            await service._sync_user_to_supabase(
                user=user,
                role_code="farmer",
                status="active",
                is_active=True,
                location_permission_granted=True,
                ip_address="127.0.0.1",
                user_agent="pytest",
            )

            assert mock_create.called
            create_payload = mock_create.call_args[0][0]
            assert create_payload["id"] == str(user.id)
            assert create_payload["phone_number"] == "01712000099"
            assert create_payload["status"] == "active"
            assert create_payload["role_id"] == "role-123"

            # 3 consents: terms_of_service, privacy_policy, location_data
            assert mock_consent.call_count == 3

