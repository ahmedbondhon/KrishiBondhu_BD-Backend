# ============================================================================
# KrishiBondhu Bangladesh — Auth & Security Tests
# Unit tests for schemas, security, OTP, passwordless login, and password reset
# ============================================================================

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    decode_token_safe,
    generate_numeric_otp,
    hash_password,
    verify_password,
)
from app.schemas.auth import (
    ExpertRegisterRequest,
    FarmerAgentRegisterRequest,
    ForgotPasswordRequest,
    LoginRequest,
    OtpLoginRequest,
    OtpLoginVerifyRequest,
    ResetPasswordRequest,
    SupportContactResponse,
    UpdateLanguageRequest,
    validate_bd_phone,
)


# --------------------------------------------------------------------------
# Test: BD Phone Number Validation
# --------------------------------------------------------------------------
class TestPhoneValidation:
    def test_valid_phone_numbers(self):
        assert validate_bd_phone("01712345678") == "01712345678"
        assert validate_bd_phone("01912345678") == "01912345678"
        assert validate_bd_phone("01312345678") == "01312345678"
        assert validate_bd_phone("01812345678") == "01812345678"

    def test_valid_with_country_code(self):
        assert validate_bd_phone("+8801712345678") == "01712345678"
        assert validate_bd_phone("8801712345678") == "01712345678"

    def test_valid_with_spaces_and_dashes(self):
        assert validate_bd_phone("017 1234 5678") == "01712345678"
        assert validate_bd_phone("017-1234-5678") == "01712345678"

    def test_invalid_phone_numbers(self):
        with pytest.raises(ValueError):
            validate_bd_phone("0121234567")  # too short
        with pytest.raises(ValueError):
            validate_bd_phone("02712345678")  # wrong prefix
        with pytest.raises(ValueError):
            validate_bd_phone("01012345678")  # 010 not valid BD operator
        with pytest.raises(ValueError):
            validate_bd_phone("abcdefghijk")


# --------------------------------------------------------------------------
# Test: Password & PIN Security
# --------------------------------------------------------------------------
class TestPasswordAndPinSecurity:
    def test_hash_and_verify_password(self):
        password = "KrishiBondhu@2026"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed) is True

    def test_hash_and_verify_pin(self):
        """Farmers often use a 4 or 6-digit numeric PIN."""
        pin = "1234"
        hashed = hash_password(pin)
        assert hashed != pin
        assert verify_password(pin, hashed) is True
        assert verify_password("9999", hashed) is False

    def test_wrong_password(self):
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_hash_is_unique(self):
        h1 = hash_password("same_pass")
        h2 = hash_password("same_pass")
        assert h1 != h2


# --------------------------------------------------------------------------
# Test: OTP Generation
# --------------------------------------------------------------------------
class TestOtpGeneration:
    def test_generate_numeric_otp(self):
        otp = generate_numeric_otp(6)
        assert len(otp) == 6
        assert otp.isdigit()

    def test_generate_4_digit_otp(self):
        otp = generate_numeric_otp(4)
        assert len(otp) == 4
        assert otp.isdigit()


# --------------------------------------------------------------------------
# Test: JWT Token Management
# --------------------------------------------------------------------------
class TestJWT:
    def test_access_token_roundtrip(self):
        user_id = uuid.uuid4()
        token = create_access_token(user_id, "farmer", "active")
        claims = decode_token(token)
        assert claims["sub"] == str(user_id)
        assert claims["role"] == "farmer"
        assert claims["status"] == "active"
        assert claims["type"] == "access"

    def test_refresh_token_roundtrip(self):
        user_id = uuid.uuid4()
        token, expires = create_refresh_token(user_id)
        claims = decode_token(token)
        assert claims["sub"] == str(user_id)
        assert claims["type"] == "refresh"
        assert "jti" in claims
        assert expires > datetime.now(timezone.utc)

    def test_refresh_token_with_remember_me_delta(self):
        user_id = uuid.uuid4()
        delta = timedelta(days=30)
        token, expires = create_refresh_token(user_id, expires_delta=delta)
        assert expires > datetime.now(timezone.utc) + timedelta(days=29)

    def test_expired_token_returns_none(self):
        user_id = uuid.uuid4()
        token = create_access_token(
            user_id, "farmer", "active",
            expires_delta=timedelta(seconds=-1),
        )
        assert decode_token_safe(token) is None


# --------------------------------------------------------------------------
# Test: Schemas for Multi-step, OTP Login, Consents & Helpline
# --------------------------------------------------------------------------
class TestAuthSchemas:
    def test_farmer_register_with_pin_and_consents(self):
        data = FarmerAgentRegisterRequest(
            full_name="রহিম উদ্দিন",
            phone_number="01712345678",
            password="123456",  # 6-digit numeric PIN
            role="farmer",
            preferred_language="bn",
            terms_accepted=True,
            location_permission_granted=True,
        )
        assert data.phone_number == "01712345678"
        assert data.password == "123456"
        assert data.role == "farmer"
        assert data.terms_accepted is True
        assert data.location_permission_granted is True

    def test_farmer_register_too_short_pin(self):
        with pytest.raises(ValueError):
            FarmerAgentRegisterRequest(
                full_name="Test",
                phone_number="01712345678",
                password="12345",  # < 6 digits
            )

    def test_farmer_register_non_numeric_pin(self):
        with pytest.raises(ValueError):
            FarmerAgentRegisterRequest(
                full_name="Test",
                phone_number="01712345678",
                password="abcdef",  # non-numeric
            )

    def test_expert_register_valid(self):
        data = ExpertRegisterRequest(
            full_name="ড. আব্দুল করিম",
            email="karim@bari.gov.bd",
            phone_number="01912345678",
            password="expertPass123",
            specialization="Plant Pathology",
            credentials="PhD BARI",
        )
        assert data.email == "karim@bari.gov.bd"

    def test_login_with_remember_me(self):
        req = LoginRequest(
            phone_number="01712345678",
            password="pass",
            remember_me=True,
        )
        assert req.remember_me is True

    def test_otp_login_request_and_verify(self):
        req = OtpLoginRequest(phone_number="01712345678")
        assert req.phone_number == "01712345678"

        verify_req = OtpLoginVerifyRequest(
            phone_number="01712345678",
            otp_code="123456",
            remember_me=True,
        )
        assert verify_req.otp_code == "123456"
        assert verify_req.remember_me is True

    def test_forgot_and_reset_password_schema(self):
        forgot = ForgotPasswordRequest(phone_number="01712345678")
        assert forgot.phone_number == "01712345678"

        reset = ResetPasswordRequest(
            phone_number="01712345678",
            otp_code="654321",
            new_password="987654",
        )
        assert reset.new_password == "987654"

    def test_language_toggle_schema(self):
        lang_bn = UpdateLanguageRequest(preferred_language="bn")
        assert lang_bn.preferred_language == "bn"

        lang_en = UpdateLanguageRequest(preferred_language="en")
        assert lang_en.preferred_language == "en"

        with pytest.raises(ValueError):
            UpdateLanguageRequest(preferred_language="fr")

    def test_support_contact_response(self):
        contact = SupportContactResponse(
            helpline_number="16123",
            support_phone="+8809612345678",
            support_email="support@krishibondhu.gov.bd",
            available_hours_bn="সকাল ৯:০০ - সন্ধ্যা ৬:০০",
            available_hours_en="9:00 AM - 6:00 PM",
        )
        assert contact.helpline_number == "16123"
        assert contact.call_center_role == "agent"
