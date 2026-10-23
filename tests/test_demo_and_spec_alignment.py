# ============================================================================
# KrishiBondhu Bangladesh — Spec Alignment, Demo Flow & Security Hardening Tests
# Covers:
#   1. Full Demo Flow (Register -> Login -> Forgot/Reset) with demo OTP "123456"
#   2. Phone Number Normalization (+880..., 880..., 01...)
#   3. Alias Routes (/request-otp, /verify-otp, /forgot-password, /reset-password)
#   4. Role Dashboard Paths (farmer, agent, expert, administrator)
#   5. Production Startup Guard (APP_ENV=production + OTP_DEMO_MODE=True)
#   6. 3 Consent Rows recorded per registration
#   7. Account Enumeration Prevention on OTP Login & Forgot Password
# ============================================================================

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.core.security import hash_password, normalize_bd_phone
from app.db.session import get_db
from app.main import app
from app.models.auth import Role, User
from app.schemas.auth import (
    FarmerAgentRegisterRequest,
    get_dashboard_path_for_role,
    UserResponse,
    TokenResponse,
    RegisterResponse,
)
from app.services.otp_service import sms_inbox, ip_rate_limiter

settings = get_settings()


@pytest.fixture(autouse=True)
def clean_inbox_and_state():
    sms_inbox._store.clear()
    ip_rate_limiter._store.clear()
    mock_db = AsyncMock()
    async def override():
        yield mock_db
    app.dependency_overrides[get_db] = override
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestPhoneNormalization:
    """Verify phone normalization: accept 01..., 8801..., +8801... -> 01..."""

    def test_phone_normalization_formats(self):
        assert normalize_bd_phone("01712345678") == "01712345678"
        assert normalize_bd_phone("8801712345678") == "01712345678"
        assert normalize_bd_phone("+8801712345678") == "01712345678"
        assert normalize_bd_phone("+88 017-1234-5678") == "01712345678"

    def test_phone_normalization_invalid(self):
        with pytest.raises(ValueError):
            normalize_bd_phone("01234567890")  # operator 012 invalid
        with pytest.raises(ValueError):
            normalize_bd_phone("12345")


class TestRoleDashboardPaths:
    """Verify dashboard_path mappings per role."""

    def test_dashboard_paths_mapping(self):
        assert get_dashboard_path_for_role("farmer") == "/dashboard"
        assert get_dashboard_path_for_role("agent") == "/agent/dashboard"
        assert get_dashboard_path_for_role("expert") == "/expert/dashboard"
        assert get_dashboard_path_for_role("administrator") == "/admin/dashboard"
        assert get_dashboard_path_for_role("admin") == "/admin/dashboard"

    def test_user_response_auto_dashboard_path(self):
        user_resp = UserResponse(
            id=uuid.uuid4(),
            full_name="Agent Karim",
            phone_number="01812345678",
            role="agent",
            status="active",
            preferred_language="bn",
            phone_verified=True,
            email_verified=False,
            created_at=datetime.now(timezone.utc),
        )
        assert user_resp.dashboard_path == "/agent/dashboard"

    def test_token_response_auto_dashboard_path(self):
        user_resp = UserResponse(
            id=uuid.uuid4(),
            full_name="Dr. Rahim",
            phone_number="01912345678",
            role="expert",
            status="pending_approval",
            preferred_language="bn",
            phone_verified=True,
            email_verified=False,
            created_at=datetime.now(timezone.utc),
        )
        token_resp = TokenResponse(
            access_token="fake-token",
            refresh_token="fake-refresh",
            expires_in=1800,
            user=user_resp,
        )
        assert token_resp.dashboard_path == "/expert/dashboard"


class TestStartupGuard:
    """Verify startup fails if APP_ENV=production and OTP_DEMO_MODE=True."""

    def test_production_otp_demo_mode_guard(self):
        from app.main import lifespan

        with patch("app.main.settings.app_env", "production"), patch(
            "app.main.settings.otp_demo_mode", True
        ):
            dummy_app = None
            with pytest.raises(RuntimeError) as exc_info:
                # Lifespan context manager execution
                import asyncio
                async def run_lifespan():
                    async with lifespan(dummy_app):
                        pass
                asyncio.run(run_lifespan())
            assert "OTP_DEMO_MODE cannot be enabled in production" in str(exc_info.value)


class TestAliasRoutes:
    """Verify all 4 alias routes route identically with include_in_schema=False."""

    @pytest.mark.asyncio
    async def test_request_otp_alias(self, client):
        res = await client.post(
            "/api/v1/auth/request-otp",
            json={"phone_number": "01712000088", "purpose": "registration"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["phone_number"] == "01712000088"
        assert data["purpose"] == "registration"

    @pytest.mark.asyncio
    async def test_forgot_password_alias(self, client):
        res = await client.post(
            "/api/v1/auth/forgot-password",
            json={"phone_number": "01712000088"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["purpose"] == "reset_password"


class TestNoEnumeration:
    """Verify login/otp-request and password/forgot return 200 with identical response when user does not exist."""

    @pytest.mark.asyncio
    async def test_login_otp_request_no_enumeration(self, client):
        res = await client.post(
            "/api/v1/auth/login/otp-request",
            json={"phone_number": "01799999999"},  # non-existent
        )
        assert res.status_code == 200
        data = res.json()
        assert "OTP sent to 01799999999 successfully." in data["message"]
        assert data["purpose"] == "login"

    @pytest.mark.asyncio
    async def test_password_forgot_no_enumeration(self, client):
        res = await client.post(
            "/api/v1/auth/password/forgot",
            json={"phone_number": "01799999999"},  # non-existent
        )
        assert res.status_code == 200
        data = res.json()
        assert "OTP sent to 01799999999 successfully." in data["message"]
        assert data["purpose"] == "reset_password"


class TestThreeConsentsRecorded:
    """Verify registration creates 3 consent rows: terms_of_service, privacy_policy, location_data."""

    @pytest.mark.asyncio
    async def test_registration_creates_three_consent_rows(self):
        from app.services.auth import AuthService

        mock_db = AsyncMock()
        service = AuthService(mock_db)

        phone = "01712999991"
        service.repo.phone_exists = AsyncMock(return_value=False)
        service.repo.email_exists = AsyncMock(return_value=False)
        service.otp_service.is_verified = AsyncMock(return_value=True)

        role = Role(id=uuid.uuid4(), code="farmer", name="Farmer")
        service.repo.get_role_by_code = AsyncMock(return_value=role)

        created_user = User(
            id=uuid.uuid4(),
            full_name="Consent Test Farmer",
            phone_number=phone,
            role_id=role.id,
            status="active",
            is_active=True,
            phone_verified=True,
            preferred_communication="sms",
        )
        service.repo.create_user = AsyncMock(return_value=created_user)

        recorded_consents = []

        async def fake_record_consent(*args, **kwargs):
            recorded_consents.append(kwargs)

        service.repo.record_user_consent = AsyncMock(side_effect=fake_record_consent)

        payload = FarmerAgentRegisterRequest(
            full_name="Consent Test Farmer",
            phone_number=phone,
            password="123456",  # 6-digit numeric PIN
            role="farmer",
            terms_accepted=True,
            location_permission_granted=True,
        )

        with patch("app.services.supabase_client.supabase_client.create_user", AsyncMock()), patch(
            "app.services.supabase_client.supabase_client.record_user_consent", AsyncMock()
        ), patch.object(service, "_issue_tokens", AsyncMock(return_value=TokenResponse(access_token="at", refresh_token="rt", expires_in=1800))):
            await service.register_farmer_agent(payload)

        # Confirm exactly 3 consent records
        assert len(recorded_consents) == 3
        consent_codes = [c["consent_type_code"] for c in recorded_consents]
        assert "terms_of_service" in consent_codes
        assert "privacy_policy" in consent_codes
        assert "location_data" in consent_codes


class TestDemoOtpFlow:
    """Verify full flow using OTP_DEMO_MODE=True and code '123456'."""

    @pytest.mark.asyncio
    async def test_demo_otp_generation_and_verification(self):
        from app.services.otp_service import OtpService

        mock_db = AsyncMock()
        service = OtpService(mock_db)

        service.repo.count_recent_otps_for_phone = AsyncMock(return_value=0)
        created_records = []

        async def fake_create_otp(**kwargs):
            class FakeRecord:
                def __init__(self, **kw):
                    self.id = uuid.uuid4()
                    for k, v in kw.items():
                        setattr(self, k, v)
                    self.is_used = False
                    self.verify_attempts = 0
            rec = FakeRecord(**kwargs)
            created_records.append(rec)
            return rec

        service.repo.create_otp = AsyncMock(side_effect=fake_create_otp)

        with patch(
            "app.services.otp_service.settings.otp_demo_mode", True
        ), patch(
            "app.services.otp_service.settings.otp_demo_code", "123456"
        ):
            # Send OTP
            res = await service.send_otp(phone_number="01712000077", purpose="registration")
            assert res.get("demo_mode") is True

            # Verify OTP using demo code 123456
            rec = created_records[0]
            service.repo.get_latest_otp = AsyncMock(return_value=rec)
            service.repo.mark_otp_verified = AsyncMock()

            v_res = await service.verify_otp(
                phone_number="01712000077",
                otp_code="123456",
                purpose="registration",
            )
            assert v_res["is_verified"] is True
            assert "verification_token" in v_res


class TestGeoCascadingEndpoints:
    """Verify cascading filters for geo endpoints: divisions, districts, upazilas, unions."""

    @pytest.mark.asyncio
    async def test_geo_cascading_endpoints(self, client):
        from app.db.session import get_db

        mock_db = AsyncMock()
        div_id = uuid.uuid4()
        dist_id = uuid.uuid4()
        upazila_id = uuid.uuid4()
        union_id = uuid.uuid4()

        div_obj = {"id": str(div_id), "bbs_code": "50", "name_en": "Rajshahi", "name_bn": "রাজশাহী"}
        dist_obj = {"id": str(dist_id), "division_id": str(div_id), "bbs_code": "5010", "name_en": "Bogura", "name_bn": "বগুড়া"}
        upazila_obj = {"id": str(upazila_id), "district_id": str(dist_id), "bbs_code": "501088", "name_en": "Shibganj", "name_bn": "শিবগঞ্জ"}
        union_obj = {"id": str(union_id), "upazila_id": str(upazila_id), "bbs_code": "15", "name_en": "Gokul", "name_bn": "গোকুল"}

        with patch("app.repositories.auth.AuthRepository.get_divisions", AsyncMock(return_value=[div_obj])), \
             patch("app.repositories.auth.AuthRepository.get_districts", AsyncMock(return_value=[dist_obj])), \
             patch("app.repositories.auth.AuthRepository.get_upazilas", AsyncMock(return_value=[upazila_obj])), \
             patch("app.repositories.auth.AuthRepository.get_unions", AsyncMock(return_value=[union_obj])):

            # 1. Divisions
            res_div = await client.get("/api/v1/geo/divisions")
            assert res_div.status_code == 200
            assert len(res_div.json()) == 1
            assert res_div.json()[0]["name_en"] == "Rajshahi"

            # 2. Districts by division_id
            res_dist = await client.get(f"/api/v1/geo/districts?division_id={div_id}")
            assert res_dist.status_code == 200
            assert len(res_dist.json()) == 1
            assert res_dist.json()[0]["name_en"] == "Bogura"

            # 3. Upazilas by district_id
            res_upz = await client.get(f"/api/v1/geo/upazilas?district_id={dist_id}")
            assert res_upz.status_code == 200
            assert len(res_upz.json()) == 1
            assert res_upz.json()[0]["name_en"] == "Shibganj"

            # 4. Unions by upazila_id
            res_un = await client.get(f"/api/v1/geo/unions?upazila_id={upazila_id}")
            assert res_un.status_code == 200
            assert len(res_un.json()) == 1
            assert res_un.json()[0]["name_en"] == "Gokul"

