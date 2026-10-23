# ============================================================================
# KrishiBondhu Bangladesh — Registration & Login Tests
# Tests the full register → login flow using mocked DB and services
# ============================================================================

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app

client = TestClient(app)


# Mock DB to skip real database connection
@pytest.fixture(autouse=True)
def setup_db_override():
    mock_db = AsyncMock()
    async def override():
        yield mock_db
    app.dependency_overrides[get_db] = override
    yield
    app.dependency_overrides.pop(get_db, None)


# Shared test data
VALID_PHONE = "01712345678"
VALID_PASSWORD = "123456"  # Numeric PIN for farmer role
VALID_NAME = "Test Farmer"

FAKE_USER_ID = str(uuid.uuid4())


def make_fake_sb_user():
    """Build a fake Supabase user dict for testing login."""
    from app.core.security import hash_password
    return {
        "id": FAKE_USER_ID,
        "phone_number": VALID_PHONE,
        "full_name": VALID_NAME,
        "email": None,
        "role_code": "farmer",
        "status": "active",
        "is_active": True,
        "phone_verified": True,
        "email_verified": False,
        "preferred_language": "bn",
        "preferred_communication": "sms",
        "avatar_url": None,
        "created_at": "2024-01-01T00:00:00+00:00",
        "password_hash": hash_password(VALID_PASSWORD),
    }


# ===========================================================================
# 1. Registration Tests
# ===========================================================================

class TestRegistration:

    @patch("app.services.auth.AuthService.register_farmer_agent", new_callable=AsyncMock)
    def test_register_valid_farmer(self, mock_register):
        """Registration with valid phone + name + PIN succeeds (201)."""
        from app.schemas.auth import TokenResponse, UserResponse
        from datetime import datetime, timezone

        fake_user = MagicMock()
        fake_user.id = uuid.UUID(FAKE_USER_ID)
        fake_user.full_name = VALID_NAME
        fake_user.phone_number = VALID_PHONE
        fake_user.email = None
        fake_user.role_code = "farmer"
        fake_user.effective_status = "active"
        fake_user.preferred_language = "bn"
        fake_user.preferred_communication = "sms"
        fake_user.avatar_url = None
        fake_user.division_id = None
        fake_user.district_id = None
        fake_user.upazila_id = None
        fake_user.union_id = None
        fake_user.village = None
        fake_user.phone_verified = True
        fake_user.email_verified = False
        fake_user.last_login_at = None
        fake_user.created_at = datetime.now(timezone.utc)

        fake_tokens = TokenResponse(
            access_token="mock.access.token",
            refresh_token="mock.refresh.token",
            token_type="bearer",
            expires_in=1800,
            user=UserResponse(
                id=uuid.UUID(FAKE_USER_ID),
                full_name=VALID_NAME,
                phone_number=VALID_PHONE,
                role="farmer",
                status="active",
                preferred_language="bn",
                preferred_communication="sms",
                phone_verified=True,
                email_verified=False,
                created_at=datetime.now(timezone.utc),
            ),
        )
        mock_register.return_value = (fake_user, fake_tokens)

        payload = {
            "phone_number": VALID_PHONE,
            "verification_token": "mock.verification.token",
            "password": VALID_PASSWORD,
            "full_name": VALID_NAME,
            "role": "farmer",
            "terms_accepted": True,
        }
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["phone_number"] == VALID_PHONE
        assert data["user"]["role"] == "farmer"
        assert "password" not in data
        assert "password_hash" not in data

    def test_register_invalid_phone(self):
        """Registration with invalid phone number is rejected (422)."""
        payload = {
            "phone_number": "12345",
            "password": VALID_PASSWORD,
            "full_name": VALID_NAME,
            "role": "farmer",
            "terms_accepted": True,
        }
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422

    def test_register_invalid_role(self):
        """Registration with a forbidden role (administrator) is rejected (422)."""
        payload = {
            "phone_number": VALID_PHONE,
            "password": "AdminPass1",
            "full_name": VALID_NAME,
            "role": "administrator",
            "terms_accepted": True,
        }
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422

    def test_register_missing_name(self):
        """Registration without full_name fails validation (422)."""
        payload = {
            "phone_number": VALID_PHONE,
            "password": VALID_PASSWORD,
            "role": "farmer",
            "terms_accepted": True,
        }
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422

    def test_register_missing_password(self):
        """Registration without password fails validation (422)."""
        payload = {
            "phone_number": VALID_PHONE,
            "full_name": VALID_NAME,
            "role": "farmer",
            "terms_accepted": True,
        }
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422

    def test_register_farmer_non_numeric_pin(self):
        """Farmer PIN must be numeric — alphabetic password fails (422)."""
        payload = {
            "phone_number": VALID_PHONE,
            "password": "abcdef",
            "full_name": VALID_NAME,
            "role": "farmer",
            "terms_accepted": True,
        }
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422

    @patch("app.services.auth.AuthService.register_farmer_agent", new_callable=AsyncMock)
    def test_register_duplicate_phone(self, mock_register):
        """Duplicate phone registration is rejected (409)."""
        from fastapi import HTTPException
        mock_register.side_effect = HTTPException(
            status_code=409,
            detail="A user with this phone_number already exists."
        )
        payload = {
            "phone_number": VALID_PHONE,
            "password": VALID_PASSWORD,
            "full_name": VALID_NAME,
            "role": "farmer",
            "terms_accepted": True,
        }
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 409
        assert "phone_number" in response.json()["detail"]


# ===========================================================================
# 2. Login Tests
# ===========================================================================

class TestLogin:

    @patch("app.services.auth.supabase_client.get_user_by_phone", new_callable=AsyncMock)
    @patch("app.services.auth.supabase_client.update_last_login", new_callable=AsyncMock)
    @patch("app.services.auth.supabase_client.record_login_attempt", new_callable=AsyncMock)
    def test_login_valid_credentials(self, mock_record, mock_update, mock_get_user):
        """Login with correct phone + password returns JWT tokens (200)."""
        mock_get_user.return_value = make_fake_sb_user()
        mock_update.return_value = True
        mock_record.return_value = None

        payload = {"phone_number": VALID_PHONE, "password": VALID_PASSWORD}
        response = client.post("/api/v1/auth/login", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["phone_number"] == VALID_PHONE
        assert "password" not in data
        assert "password_hash" not in data

    @patch("app.services.auth.supabase_client.get_user_by_phone", new_callable=AsyncMock)
    @patch("app.services.auth.supabase_client.record_login_attempt", new_callable=AsyncMock)
    def test_login_wrong_password(self, mock_record, mock_get_user):
        """Login with wrong password returns 401."""
        mock_get_user.return_value = make_fake_sb_user()
        mock_record.return_value = None

        payload = {"phone_number": VALID_PHONE, "password": "999999"}
        response = client.post("/api/v1/auth/login", json=payload)
        assert response.status_code == 401

    @patch("app.services.auth.AuthService.login", new_callable=AsyncMock)
    @patch("app.services.auth.supabase_client.get_user_by_phone", new_callable=AsyncMock)
    def test_login_nonexistent_user(self, mock_get_user, mock_login):
        """Login with phone that doesn't exist returns 401."""
        from fastapi import HTTPException
        mock_get_user.return_value = None
        mock_login.side_effect = HTTPException(
            status_code=401,
            detail="Invalid phone number, email, or password/PIN."
        )
        payload = {"phone_number": "01811111111", "password": "123456"}
        response = client.post("/api/v1/auth/login", json=payload)
        assert response.status_code == 401

    def test_login_missing_identifier(self):
        """Login without phone or email returns 422."""
        payload = {"password": VALID_PASSWORD}
        response = client.post("/api/v1/auth/login", json=payload)
        assert response.status_code == 422

    def test_login_missing_password(self):
        """Login without password returns 422."""
        payload = {"phone_number": VALID_PHONE}
        response = client.post("/api/v1/auth/login", json=payload)
        assert response.status_code == 422

    @patch("app.services.auth.supabase_client.get_user_by_phone", new_callable=AsyncMock)
    @patch("app.services.auth.supabase_client.record_login_attempt", new_callable=AsyncMock)
    def test_login_inactive_account(self, mock_record, mock_get_user):
        """Login with inactive/pending account returns 403."""
        inactive_user = make_fake_sb_user()
        inactive_user["status"] = "pending_approval"
        inactive_user["is_active"] = False
        mock_get_user.return_value = inactive_user
        mock_record.return_value = None

        payload = {"phone_number": VALID_PHONE, "password": VALID_PASSWORD}
        response = client.post("/api/v1/auth/login", json=payload)
        assert response.status_code == 403


# ===========================================================================
# 3. Password Hash Verification
# ===========================================================================

class TestPasswordHashing:

    def test_password_is_hashed_not_plain(self):
        """Verify bcrypt hash is NOT the plain password string."""
        from app.core.security import hash_password
        plain = "123456"
        hashed = hash_password(plain)
        assert hashed != plain
        assert hashed.startswith(("$2b$", "$argon2id$"))

    def test_verify_correct_password(self):
        """Correct password verifies against its hash."""
        from app.core.security import hash_password, verify_password
        plain = "123456"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_wrong_password(self):
        """Wrong password does not verify against the hash."""
        from app.core.security import hash_password, verify_password
        hashed = hash_password("123456")
        assert verify_password("654321", hashed) is False
