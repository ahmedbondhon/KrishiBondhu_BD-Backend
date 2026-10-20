# ============================================================================
# KrishiBondhu Bangladesh — Core Configuration
# Pydantic v2 Settings with .env support
# ============================================================================

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "KrishiBondhu Bangladesh"
    app_env: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    cors_allowed_origins: str = "*"  # Comma-separated or "*"

    # --- Supabase & Storage (load from .env, never hardcode secrets) ---
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    storage_bucket_name: str = "krishibondhu-uploads"
    enable_supabase_auth_fallback: bool = True  # Can be disabled in production via env

    # --- Database ---
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/krishibondhu"
    database_echo: bool = False

    # --- JWT (load from .env) ---
    jwt_secret_key: str = "change-me-to-a-long-random-string"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    remember_me_refresh_token_expire_days: int = 30

    # --- Security & Lockout ---
    max_login_attempts: int = 5
    login_lockout_minutes: int = 15

    # --- Password Policy Constants ---
    farmer_pin_min_len: int = 6  # FARMER_PIN_MIN_LEN: numeric PIN, min length 6
    privileged_password_min_len: int = 8  # Min 8 chars with upper, lower, digit

    # --- OTP & SMS ---
    otp_length: int = 6
    otp_expire_minutes: int = 5
    otp_mock_sms: bool = True  # Legacy flag, replaced by sms_mode
    sms_api_key: str | None = None
    sms_sender_id: str | None = None

    # --- OTP Security & Demo Mode ---
    otp_hmac_secret: str = "change-me-otp-hmac-secret"  # HMAC key for hashing OTPs
    otp_max_verify_attempts: int = 5  # Max wrong attempts before OTP invalidated
    otp_demo_mode: bool = False  # If True, generates fixed demo OTP (never enable in production)
    otp_demo_code: str = "123456"  # Fixed code used when otp_demo_mode is True

    # --- SMS Simulator ---
    # "simulator" = store OTP in fake inbox for frontend popup
    # "disabled"  = no SMS, OTP only in server logs (default)
    sms_mode: str = "disabled"

    # --- OTP Rate Limits ---
    otp_rate_limit_per_phone: int = 3   # Max OTPs per phone in window
    otp_rate_limit_per_ip: int = 10     # Max OTPs per IP in window
    otp_rate_limit_window_minutes: int = 10  # Window size in minutes

    # --- Support & Helpline ---
    support_helpline: str = "16123"  # Bangladesh Agricultural Call Center
    support_phone: str = "+8809612345678"
    support_email: str = "support@krishibondhu.gov.bd"
    support_available_hours_bn: str = "সকাল ৯:০০ - সন্ধ্যা ৬:০০ (শনিবার থেকে বৃহস্পতিবার)"
    support_available_hours_en: str = "9:00 AM - 6:00 PM (Saturday to Thursday)"

    # --- Timezone ---
    display_timezone: str = "Asia/Dhaka"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
