# ============================================================================
# KrishiBondhu Bangladesh — Auth API Integration Tests
# Tests HTTP endpoints for OTP dispatch, verify, helpline, and health
# ============================================================================

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app

client = TestClient(app)


# Mock DB Dependency to isolate API tests from database server
@pytest.fixture(autouse=True)
def setup_db_override():
    mock_db = AsyncMock()
    async def override():
        yield mock_db
    app.dependency_overrides[get_db] = override
    yield
    app.dependency_overrides.pop(get_db, None)



class TestAuthApiEndpoints:
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_support_hotline_endpoint(self):
        response = client.get("/api/v1/auth/support")
        assert response.status_code == 200
        data = response.json()
        assert data["helpline_number"] == "16123"
        assert "call_center_role" in data
        assert "available_hours_bn" in data

    @patch("app.services.otp_service.OtpService.send_otp")
    def test_send_otp_endpoint(self, mock_send_otp):
        mock_send_otp.return_value = {
            "message": "OTP sent to 01712345678 successfully.",
            "phone_number": "01712345678",
            "purpose": "registration",
            "expires_in_seconds": 300,
            "resend_after": 60,
        }

        payload = {"phone_number": "01712345678", "purpose": "registration"}
        response = client.post("/api/v1/auth/otp/send", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["phone_number"] == "01712345678"
        assert "dev_otp_code" not in data
        assert data["resend_after"] == 60

    @patch("app.services.otp_service.OtpService.verify_otp")
    def test_verify_otp_endpoint(self, mock_verify_otp):
        mock_verify_otp.return_value = {
            "message": "OTP verified successfully.",
            "phone_number": "01712345678",
            "is_verified": True,
            "verification_token": "mock.jwt.token",
        }

        payload = {
            "phone_number": "01712345678",
            "otp_code": "123456",
            "purpose": "registration",
        }
        response = client.post("/api/v1/auth/otp/verify", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["is_verified"] is True
        assert data["verification_token"] == "mock.jwt.token"

    def test_send_otp_invalid_phone(self):
        payload = {"phone_number": "12345", "purpose": "registration"}
        response = client.post("/api/v1/auth/otp/send", json=payload)
        assert response.status_code == 422  # Pydantic validation error

    @patch("app.services.auth.AuthService.forgot_password_request")
    def test_forgot_password_endpoint(self, mock_forgot):
        mock_forgot.return_value = {
            "message": "OTP sent to 01712345678 successfully.",
            "phone_number": "01712345678",
            "purpose": "reset_password",
            "expires_in_seconds": 300,
            "resend_after": 60,
        }

        payload = {"phone_number": "01712345678"}
        response = client.post("/api/v1/auth/password/forgot", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["purpose"] == "reset_password"
        assert "dev_otp_code" not in data

    @patch("app.services.auth.AuthService.request_otp_login")
    def test_otp_login_request_endpoint(self, mock_req_login):
        mock_req_login.return_value = {
            "message": "OTP sent to 01712345678 successfully.",
            "phone_number": "01712345678",
            "purpose": "login",
            "expires_in_seconds": 300,
            "resend_after": 60,
        }

        payload = {"phone_number": "01712345678"}
        response = client.post("/api/v1/auth/login/otp-request", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["purpose"] == "login"
        assert "dev_otp_code" not in data

