"""
core/config.py
==============
Application-wide settings loaded from environment variables using Pydantic Settings.

How it works:
  - All settings are read from the `.env` file (or actual environment variables).
  - `get_settings()` is cached with `@lru_cache` so the `.env` file is parsed
    only once per process, not on every request.
  - Import `settings` anywhere in the app for typed access to configuration.

Usage:
    from app.core.config import settings
    print(settings.database_url)
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "KrishiBondhu Bangladesh API"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000

    # --- Database ---
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/krishibondhu_db"
    database_url_sync: str = "postgresql+psycopg2://postgres:password@localhost:5432/krishibondhu_db"

    # --- JWT ---
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 30
    farmer_pin_min_len: int = 6
    privileged_password_min_len: int = 8
    # --- Object Storage ---
    storage_provider: str = "supabase"         # 'supabase' | 's3' | 'cloudinary'
    storage_bucket_name: str = "krishibondhu-uploads"
    storage_signed_url_expiry_seconds: int = 3600
    upload_dir: str = "uploads"
    max_file_size_bytes: int = 2 * 1024 * 1024
    public_base_url: str = "http://localhost:8000"

    enable_supabase_auth_fallback: bool = True
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    remember_me_refresh_token_expire_days: int = 30
    max_login_attempts: int = 5
    login_lockout_minutes: int = 15

    # --- OTP & SMS ---
    otp_length: int = 6
    otp_expire_minutes: int = 5
    otp_mock_sms: bool = True
    sms_api_key: Optional[str] = None
    sms_sender_id: Optional[str] = None
    otp_hmac_secret: str = "change-me-otp-hmac-secret"
    otp_max_verify_attempts: int = 5
    otp_demo_mode: bool = True
    otp_demo_code: str = "123456"
    sms_mode: str = "simulator"
    otp_rate_limit_per_phone: int = 3
    otp_rate_limit_per_ip: int = 10
    otp_rate_limit_window_minutes: int = 10

    # --- Support & Helpline ---
    support_helpline: str = "16123"
    support_phone: str = "+8809612345678"
    support_email: str = "support@krishibondhu.gov.bd"
    support_available_hours_bn: str = "সকাল ৯:০০ - সন্ধ্যা ৬:০০ (শনিবার থেকে বৃহস্পতিবার)"
    support_available_hours_en: str = "9:00 AM - 6:00 PM (Saturday to Thursday)"
    display_timezone: str = "Asia/Dhaka"
    app_env: str = "development"



    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_role_key: str = ""
    supabase_project_ref: str = ""

    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "ap-southeast-1"
    aws_s3_bucket: str = ""

    # --- AI Service (Internal) ---
    ai_service_url: str = "http://localhost:8001"
    ai_confidence_threshold: float = 0.65  # Below this -> escalate to human expert

    # --- CORS ---
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # --- Timezone ---
    timezone: str = "Asia/Dhaka"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Allow CORS origins as a JSON list string or an actual list."""
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v


@lru_cache()
def get_settings() -> Settings:
    """Return a cached Settings instance (read .env once per process)."""
    return Settings()


# Module-level convenience singleton
settings = get_settings()
