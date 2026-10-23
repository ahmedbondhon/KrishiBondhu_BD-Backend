"""
tests/test_auth_system.py
=========================
Comprehensive automated tests for KrishiBondhu Authentication Module:
- Phone number normalization (all BD operators, formats, Bengali numerals)
- Pydantic v2 schemas and validation
- Cryptographic security (Argon2 password hashing, JWT tokens)
- AuthService business logic
- FastAPI HTTP API endpoints
"""

import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from jose import jwt

import sys
sys.path.insert(0, "backend")

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    normalize_bd_phone,
    verify_access_token,
    verify_password,
    verify_refresh_token,
)
from app.core.dependencies import get_db
from app.main import app
from app.models.auth import Role, User
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    RoleResponse,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)
from app.services.auth_service import AuthService


# ─────────────────────────────────────────────────────────────────────────────
# 1. PHONE NUMBER NORMALIZATION TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestPhoneNumberNormalization:
    """Tests for normalize_bd_phone function handling all possible BD phone formats."""

    @pytest.mark.parametrize("phone,expected", [
        # Standard local 11 digits
        ("01712345678", "+8801712345678"),
        ("01812345678", "+8801812345678"),
        ("01912345678", "+8801912345678"),
        ("01512345678", "+8801512345678"),
        ("01312345678", "+8801312345678"),
        ("01412345678", "+8801412345678"),
        ("01612345678", "+8801612345678"),

        # International with +
        ("+8801712345678", "+8801712345678"),
        ("+8801812345678", "+8801812345678"),
        ("+8801912345678", "+8801912345678"),
        ("+8801512345678", "+8801512345678"),
        ("+8801312345678", "+8801312345678"),
        ("+8801412345678", "+8801412345678"),
        ("+8801612345678", "+8801612345678"),

        # International without +
        ("8801712345678", "+8801712345678"),
        ("8801812345678", "+8801812345678"),
        ("8801512345678", "+8801512345678"),

        # Dialing prefix 00880
        ("008801712345678", "+8801712345678"),
        ("008801812345678", "+8801812345678"),

        # 10 digits without leading 0
        ("1712345678", "+8801712345678"),
        ("1812345678", "+8801812345678"),
        ("1512345678", "+8801512345678"),

        # Separators: hyphens, spaces, dots, parentheses
        ("017-1234-5678", "+8801712345678"),
        ("017 1234 5678", "+8801712345678"),
        ("+880 17 1234 5678", "+8801712345678"),
        ("+880-17-1234-5678", "+8801712345678"),
        ("(+880) 1712345678", "+8801712345678"),
        ("(017) 1234-5678", "+8801712345678"),
        ("017.1234.5678", "+8801712345678"),
        ("  01712345678  ", "+8801712345678"),

        # Bengali Numerals
        ("০১৭১২৩৪৫৬৭৮", "+8801712345678"),
        ("+৮৮০১৭১২৩৪৫৬৭৮", "+8801712345678"),
        ("৮৮০১৭১২৩৪৫৬৭৮", "+8801712345678"),
        ("০১৭-১২৩৪-৫৬৭৮", "+8801712345678"),
        ("০১৭ ১২৩৪ ৫৬৭৮", "+8801712345678"),
        ("০১৮১২৩৪৫৬৭৮", "+8801812345678"),
        ("০১৫১২৩৪৫৬৭৮", "+8801512345678"),

        # Integer input
        (1712345678, "+8801712345678"),
    ])
    def test_valid_phone_formats(self, phone, expected):
        assert normalize_bd_phone(phone) == expected

    @pytest.mark.parametrize("invalid_phone", [
        "",                     # empty string
        "   ",                  # whitespace
        None,                   # None
        "12345",                # too short
        "0171234567",           # 10 digits starting with 0 (missing 1 digit)
        "017123456789",         # 12 digits (too long)
        "0171234abcd",          # contains letters
        "phone_number",         # words
        "+14155552671",         # US number
        "+919876543210",        # Indian number
        "02123456789",          # Landline prefix (02)
        "+---()./",             # punctuation only
    ])
    def test_invalid_phone_formats(self, invalid_phone):
        with pytest.raises(ValueError):
            normalize_bd_phone(invalid_phone)


# ─────────────────────────────────────────────────────────────────────────────
# 2. PYDANTIC SCHEMA VALIDATION TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestAuthSchemas:
    """Tests for RegisterRequest, LoginRequest, and other auth DTOs."""

    def test_register_request_normalizes_phone(self):
        req = RegisterRequest(
            phone_number="01754890387",
            password="Test@12345",
            full_name="Md. Karim",
        )
        assert req.phone_number == "+8801754890387"
        assert req.role_code == "farmer"  # Default role

    def test_register_request_accepts_all_operators(self):
        for op in ["013", "014", "015", "016", "017", "018", "019"]:
            req = RegisterRequest(
                phone_number=f"{op}12345678",
                password="TestPassword123",
                full_name="Farmer Test",
            )
            assert req.phone_number == f"+88{op}12345678"

    @pytest.mark.parametrize("valid_password", [
        "Test@12345",       # 10 chars, mixed
        "Password123!",     # 12 chars, mixed
        "abc12345",         # 8 chars, lowercase + digit
        "123456",           # 6 chars, numeric PIN
        "farmer_pass",      # 11 chars, underscore
        "a" * 128,          # boundary: exactly 128 characters
        "পাসওয়ার্ড১২৩",     # Unicode Bangla password >= 6 chars
    ])
    def test_register_request_valid_passwords(self, valid_password):
        req = RegisterRequest(
            phone_number="01712345678",
            password=valid_password,
            full_name="Test User",
        )
        assert req.password == valid_password

    @pytest.mark.parametrize("invalid_password", [
        "12345",            # 5 chars: too short
        "",                 # empty string
        "a" * 129,          # 129 chars: too long
    ])
    def test_register_request_invalid_passwords(self, invalid_password):
        with pytest.raises(Exception):
            RegisterRequest(
                phone_number="01712345678",
                password=invalid_password,
                full_name="Test User",
            )

    @pytest.mark.parametrize("invalid_name", [
        "A",                # length 1: too short
        "",                 # empty
        "A" * 151,          # length 151: too long
    ])
    def test_register_request_invalid_full_name(self, invalid_name):
        with pytest.raises(Exception):
            RegisterRequest(
                phone_number="01712345678",
                password="ValidPassword123",
                full_name=invalid_name,
            )

    def test_login_request_normalizes_phone(self):
        req = LoginRequest(phone_number="01812345678", password="Password123")
        assert req.phone_number == "+8801812345678"

        req_bangla = LoginRequest(phone_number="০১৮১২৩৪৫৬৭৮", password="Password123")
        assert req_bangla.phone_number == "+8801812345678"

    def test_login_request_requires_password(self):
        with pytest.raises(Exception):
            LoginRequest(phone_number="01712345678", password="")


# ─────────────────────────────────────────────────────────────────────────────
# 3. CRYPTOGRAPHIC SECURITY TESTS (Argon2 & JWT)
# ─────────────────────────────────────────────────────────────────────────────

class TestSecurityFunctions:
    """Tests for password hashing and JWT encoding/decoding."""

    def test_password_hashing_and_verification(self):
        raw_password = "SecretPassword@2026"
        hashed = hash_password(raw_password)

        assert hashed != raw_password
        assert hashed.startswith(("$argon2", "$2b$", "$2a$"))

        # Correct password verifies
        assert verify_password(raw_password, hashed) is True

        # Incorrect password fails
        assert verify_password("WrongPassword@2026", hashed) is False
        assert verify_password("secretpassword@2026", hashed) is False  # Case sensitive

    def test_jwt_access_token_creation_and_verification(self):
        user_id = uuid.uuid4()
        role = "expert"

        token = create_access_token(user_id=user_id, role_code=role)
        assert isinstance(token, str)

        payload = verify_access_token(token)
        assert payload is not None
        assert payload["sub"] == str(user_id)
        assert payload["role"] == role
        assert payload["typ"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_jwt_refresh_token_creation_and_verification(self):
        user_id = uuid.uuid4()

        token = create_refresh_token(user_id=user_id)
        assert isinstance(token, str)

        extracted_id = verify_refresh_token(token)
        assert extracted_id == str(user_id)

    def test_token_type_separation_security(self):
        """Access token must NOT be accepted as refresh token, and vice versa."""
        user_id = uuid.uuid4()
        access_tok = create_access_token(user_id, "farmer")
        refresh_tok = create_refresh_token(user_id)

        # Access token used where refresh token expected -> None
        assert verify_refresh_token(access_tok) is None

        # Refresh token used where access token expected -> None
        assert verify_access_token(refresh_tok) is None

    def test_tampered_token_is_rejected(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id, "farmer")

        # Tamper token signature
        tampered = token[:-5] + "XXXXX"
        assert verify_access_token(tampered) is None

    def test_expired_token_is_rejected(self):
        user_id = uuid.uuid4()
        expired_payload = {
            "sub": str(user_id),
            "role": "farmer",
            "typ": "access",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
            "iat": datetime.now(timezone.utc) - timedelta(minutes=10),
        }
        expired_token = jwt.encode(
            expired_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )
        assert verify_access_token(expired_token) is None


# ─────────────────────────────────────────────────────────────────────────────
# 4. AUTH SERVICE BUSINESS LOGIC TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestAuthService:
    """Tests for AuthService business rules: duplicates, roles, authentication."""

    @pytest.mark.asyncio
    async def test_register_duplicate_phone_raises_409(self):
        service = AuthService()
        mock_db = AsyncMock()

        # Mock existing user found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = User(
            id=uuid.uuid4(),
            phone_number="+8801754890387",
            full_name="Existing User",
        )
        mock_db.execute.return_value = mock_result

        payload = RegisterRequest(
            phone_number="01754890387",
            password="Test@12345",
            full_name="New User",
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.register_user(mock_db, payload)

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["code"] == "PHONE_ALREADY_REGISTERED"

    @pytest.mark.asyncio
    async def test_register_invalid_role_raises_400(self):
        service = AuthService()
        mock_db = AsyncMock()

        # Step 1: No duplicate user found
        mock_existing = MagicMock()
        mock_existing.scalar_one_or_none.return_value = None

        # Step 2: Role query returns None
        mock_role = MagicMock()
        mock_role.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [mock_existing, mock_role]

        payload = RegisterRequest(
            phone_number="01754890388",
            password="Test@12345",
            full_name="New User",
            role_code="non_existent_role",
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.register_user(mock_db, payload)

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["code"] == "INVALID_ROLE"

    @pytest.mark.asyncio
    async def test_register_success(self):
        service = AuthService()
        mock_db = AsyncMock()

        mock_existing = MagicMock()
        mock_existing.scalar_one_or_none.return_value = None

        fake_role = Role(id=uuid.uuid4(), code="farmer", name="কৃষক")
        mock_role = MagicMock()
        mock_role.scalar_one_or_none.return_value = fake_role

        mock_db.execute.side_effect = [mock_existing, mock_role]

        payload = RegisterRequest(
            phone_number="01754890388",
            password="Password123!",
            full_name="Rahim Mia",
            role_code="farmer",
        )

        user = await service.register_user(mock_db, payload)
        assert user.phone_number == "+8801754890388"
        assert user.full_name == "Rahim Mia"
        assert verify_password("Password123!", user.password_hash) is True
        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_authenticate_invalid_credentials(self):
        service = AuthService()
        mock_db = AsyncMock()

        # Case 1: Phone not found
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_res

        with pytest.raises(HTTPException) as exc_info:
            await service.authenticate(mock_db, "+8801711111111", "some_pass")
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["code"] == "INVALID_CREDENTIALS"

        # Case 2: Wrong password
        fake_role = Role(id=uuid.uuid4(), code="farmer", name="কৃষক")
        fake_user = User(
            id=uuid.uuid4(),
            phone_number="+8801754890387",
            password_hash=hash_password("CorrectPass123"),
            is_active=True,
            is_deleted=False,
            role=fake_role,
        )
        mock_res.scalar_one_or_none.return_value = fake_user

        with pytest.raises(HTTPException) as exc_info:
            await service.authenticate(mock_db, "+8801754890387", "WrongPass123")
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["code"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_authenticate_inactive_account_raises_403(self):
        service = AuthService()
        mock_db = AsyncMock()

        fake_role = Role(id=uuid.uuid4(), code="farmer", name="কৃষক")
        inactive_user = User(
            id=uuid.uuid4(),
            phone_number="+8801754890387",
            password_hash=hash_password("CorrectPass123"),
            is_active=False,  # Inactive
            is_deleted=False,
            role=fake_role,
        )
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = inactive_user
        mock_db.execute.return_value = mock_res

        with pytest.raises(HTTPException) as exc_info:
            await service.authenticate(mock_db, "+8801754890387", "CorrectPass123")
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == "ACCOUNT_DISABLED"

    @pytest.mark.asyncio
    async def test_authenticate_success(self):
        service = AuthService()
        mock_db = AsyncMock()

        fake_role = Role(id=uuid.uuid4(), code="farmer", name="কৃষক")
        active_user = User(
            id=uuid.uuid4(),
            phone_number="+8801754890387",
            password_hash=hash_password("CorrectPass123"),
            is_active=True,
            is_deleted=False,
            role=fake_role,
        )
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = active_user
        mock_db.execute.return_value = mock_res

        access_token, refresh_token = await service.authenticate(
            mock_db, "+8801754890387", "CorrectPass123"
        )
        assert verify_access_token(access_token)["sub"] == str(active_user.id)
        assert verify_refresh_token(refresh_token) == str(active_user.id)


# ─────────────────────────────────────────────────────────────────────────────
# 5. FASTAPI HTTP ROUTE ENDPOINT INTEGRATION TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestAuthHttpEndpoints:
    """Simulated HTTP tests for /api/v1/auth routes using FastAPI TestClient."""

    @pytest.fixture(autouse=True)
    def setup_client(self):
        self.mock_db = AsyncMock()

        async def override_get_db():
            yield self.mock_db

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)
        yield
        app.dependency_overrides.clear()

    def test_post_register_endpoint_201_success(self):
        fake_role = Role(id=uuid.uuid4(), code="farmer", name="কৃষক")
        fake_user = User(
            id=uuid.uuid4(),
            phone_number="+8801754890387",
            password_hash=hash_password("Test@12345"),
            full_name="Md. Abdullah",
            is_active=True,
            role_id=fake_role.id,
            role=fake_role,
            preferred_language="bn",
        )

        with patch.object(AuthService, "register_user", new_callable=AsyncMock) as mock_reg:
            mock_reg.return_value = fake_user

            # Test using local 017 format in JSON payload
            payload = {
                "phone_number": "01754890387",
                "password": "Test@12345",
                "full_name": "Md. Abdullah",
            }
            resp = self.client.post("/api/v1/auth/register", json=payload)
            assert resp.status_code == 201
            body = resp.json()
            assert body["success"] is True
            assert body["data"]["phone_number"] == "+8801754890387"
            assert body["data"]["full_name"] == "Md. Abdullah"
            assert "password" not in body["data"]
            assert "password_hash" not in body["data"]

    def test_post_register_endpoint_rejects_invalid_inputs_422(self):
        # 1. Invalid phone number (too short)
        resp1 = self.client.post("/api/v1/auth/register", json={
            "phone_number": "12345",
            "password": "Password123!",
            "full_name": "Abdullah",
        })
        assert resp1.status_code == 422

        # 2. Invalid password (< 6 chars)
        resp2 = self.client.post("/api/v1/auth/register", json={
            "phone_number": "01754890387",
            "password": "12345",
            "full_name": "Abdullah",
        })
        assert resp2.status_code == 422

        # 3. Missing full_name
        resp3 = self.client.post("/api/v1/auth/register", json={
            "phone_number": "01754890387",
            "password": "Password123!",
        })
        assert resp3.status_code == 422

    def test_post_login_endpoint_200_success(self):
        fake_user_id = uuid.uuid4()
        access_tok = create_access_token(fake_user_id, "farmer")
        refresh_tok = create_refresh_token(fake_user_id)

        with patch.object(AuthService, "authenticate", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = (access_tok, refresh_tok)

            payload = {
                "phone_number": "01754890387",  # local format allowed
                "password": "Test@12345",
            }
            resp = self.client.post("/api/v1/auth/login", json=payload)
            assert resp.status_code == 200
            body = resp.json()
            assert body["success"] is True
            assert body["data"]["access_token"] == access_tok
            assert body["data"]["refresh_token"] == refresh_tok
            assert body["data"]["token_type"] == "Bearer"
            assert body["data"]["expires_in_minutes"] == settings.jwt_access_token_expire_minutes

    def test_post_login_endpoint_401_on_bad_credentials(self):
        with patch.object(AuthService, "authenticate", new_callable=AsyncMock) as mock_auth:
            mock_auth.side_effect = HTTPException(
                status_code=401,
                detail={"code": "INVALID_CREDENTIALS", "message_bn": "ফোন নম্বর বা পাসওয়ার্ড ভুল।"},
            )

            resp = self.client.post("/api/v1/auth/login", json={
                "phone_number": "01754890387",
                "password": "WrongPassword",
            })
            assert resp.status_code == 401
            assert resp.json()["detail"]["code"] == "INVALID_CREDENTIALS"

    def test_post_refresh_token_200_success(self):
        new_access = "new.access.token"
        new_refresh = "new.refresh.token"

        with patch.object(AuthService, "refresh_tokens", new_callable=AsyncMock) as mock_ref:
            mock_ref.return_value = (new_access, new_refresh)

            resp = self.client.post("/api/v1/auth/refresh", json={
                "refresh_token": "valid.old.refresh.token"
            })
            assert resp.status_code == 200
            body = resp.json()
            assert body["data"]["access_token"] == new_access
            assert body["data"]["refresh_token"] == new_refresh

    def test_get_me_endpoint_200_success(self):
        fake_user_id = uuid.uuid4()
        fake_role = Role(id=uuid.uuid4(), code="farmer", name="কৃষক")
        fake_user = User(
            id=fake_user_id,
            phone_number="+8801754890387",
            password_hash=hash_password("Test@12345"),
            full_name="Md. Abdullah",
            is_active=True,
            is_deleted=False,
            role_id=fake_role.id,
            role=fake_role,
            preferred_language="bn",
        )
        token = create_access_token(fake_user_id, "farmer")

        # Mock db query inside get_current_user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = fake_user
        self.mock_db.execute.return_value = mock_result

        with patch.object(AuthService, "get_user_with_role", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = fake_user

            resp = self.client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["success"] is True
            assert body["data"]["phone_number"] == "+8801754890387"
            assert body["data"]["role"]["code"] == "farmer"

    def test_get_me_endpoint_unauthorized_without_token(self):
        resp = self.client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_post_me_profile_update_200_success(self):
        fake_user_id = uuid.uuid4()
        fake_role = Role(id=uuid.uuid4(), code="farmer", name="কৃষক")
        fake_user = User(
            id=fake_user_id,
            phone_number="+8801754890387",
            password_hash=hash_password("Test@12345"),
            full_name="Md. Updated Abdullah",
            is_active=True,
            is_deleted=False,
            role_id=fake_role.id,
            role=fake_role,
            preferred_language="en",
        )
        token = create_access_token(fake_user_id, "farmer")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = fake_user
        self.mock_db.execute.return_value = mock_result

        with patch.object(AuthService, "update_profile", new_callable=AsyncMock) as mock_up, \
             patch.object(AuthService, "get_user_with_role", new_callable=AsyncMock) as mock_get:
            mock_up.return_value = fake_user
            mock_get.return_value = fake_user

            resp = self.client.post(
                "/api/v1/auth/me/profile",
                headers={"Authorization": f"Bearer {token}"},
                json={"full_name": "Md. Updated Abdullah", "preferred_language": "en"},
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["data"]["full_name"] == "Md. Updated Abdullah"
            assert body["data"]["preferred_language"] == "en"

