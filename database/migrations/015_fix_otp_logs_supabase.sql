-- ============================================================================
-- Migration 015: Fix otp_logs table schema in Supabase (Bug 8)
-- ============================================================================
-- Problem: Supabase's auth.otp_logs table may be missing columns that the
-- application code expects (otp_hash, verify_attempts, is_used).
-- This causes server-side warnings and potential write failures.
--
-- Run this migration against your Supabase project to bring the table schema
-- in sync with the application's local ORM model (app/models/auth.py OtpLog).
-- ============================================================================

-- Add otp_hash column if not present (Bug 8 core fix)
ALTER TABLE auth.otp_logs
    ADD COLUMN IF NOT EXISTS otp_hash VARCHAR(128);

-- Add verify_attempts column if not present (needed for OTP attempt limits)
ALTER TABLE auth.otp_logs
    ADD COLUMN IF NOT EXISTS verify_attempts INT DEFAULT 0 NOT NULL;

-- Add is_used column if not present (needed for single-use enforcement)
ALTER TABLE auth.otp_logs
    ADD COLUMN IF NOT EXISTS is_used BOOLEAN DEFAULT FALSE NOT NULL;

-- Add is_verified column if not present
ALTER TABLE auth.otp_logs
    ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE NOT NULL;

-- Add purpose column if not present
ALTER TABLE auth.otp_logs
    ADD COLUMN IF NOT EXISTS purpose VARCHAR(50) DEFAULT 'registration' NOT NULL;

-- Add expires_at column if not present
ALTER TABLE auth.otp_logs
    ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ;

-- Index: fast lookup for active OTPs by phone + purpose (avoids full-table scans)
CREATE INDEX IF NOT EXISTS idx_otp_logs_phone_purpose_active
    ON auth.otp_logs (phone_number, purpose, is_used, created_at DESC);

-- ============================================================================
-- Verify: After running, check with:
--   SELECT column_name, data_type FROM information_schema.columns
--   WHERE table_schema = 'auth' AND table_name = 'otp_logs';
-- Expected columns: id, phone_number, otp_code, otp_hash, purpose,
--                   is_verified, is_used, verify_attempts, expires_at, created_at
-- ============================================================================
