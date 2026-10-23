"""Add OTP security enhancements and audit.admin_actions table

Revision ID: 002_otp_security_and_audit
Revises: 001_auth_module
Create Date: 2026-10-17
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers
revision: str = "002_otp_security_and_audit"
down_revision: Union[str, None] = "001_auth_module"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Update auth.otp_logs: add otp_hash, verify_attempts, is_used
    # ------------------------------------------------------------------
    op.execute("""
        DO $$
        BEGIN
            -- Make legacy otp_code column nullable (plain code is no longer stored)
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'auth' AND table_name = 'otp_logs' AND column_name = 'otp_code'
            ) THEN
                ALTER TABLE auth.otp_logs ALTER COLUMN otp_code DROP NOT NULL;
            END IF;

            -- Add otp_hash column for HMAC-SHA256 hashed OTPs
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'auth' AND table_name = 'otp_logs' AND column_name = 'otp_hash'
            ) THEN
                ALTER TABLE auth.otp_logs ADD COLUMN otp_hash VARCHAR(128);
            END IF;

            -- Add verify_attempts counter for brute-force protection
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'auth' AND table_name = 'otp_logs' AND column_name = 'verify_attempts'
            ) THEN
                ALTER TABLE auth.otp_logs ADD COLUMN verify_attempts INT DEFAULT 0 NOT NULL;
            END IF;

            -- Add is_used flag for single-use enforcement
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'auth' AND table_name = 'otp_logs' AND column_name = 'is_used'
            ) THEN
                ALTER TABLE auth.otp_logs ADD COLUMN is_used BOOLEAN DEFAULT FALSE NOT NULL;
            END IF;
        END $$;
    """)

    # ------------------------------------------------------------------
    # 2. Initialize audit schema and audit.admin_actions table
    # ------------------------------------------------------------------
    op.execute("CREATE SCHEMA IF NOT EXISTS audit")

    op.execute("""
        CREATE TABLE IF NOT EXISTS audit.admin_actions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            actor_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
            action VARCHAR(100) NOT NULL,
            target_id UUID NULL,
            target_type VARCHAR(100) DEFAULT 'user',
            details JSONB NULL,
            ip_address VARCHAR(50) NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
        );
    """)

    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_admin_actions_actor ON audit.admin_actions(actor_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_admin_actions_action ON audit.admin_actions(action)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_admin_actions_target ON audit.admin_actions(target_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_admin_actions_created ON audit.admin_actions(created_at DESC)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS audit.admin_actions")
    op.execute("DROP SCHEMA IF EXISTS audit CASCADE")

    op.execute("""
        ALTER TABLE auth.otp_logs DROP COLUMN IF EXISTS is_used;
        ALTER TABLE auth.otp_logs DROP COLUMN IF EXISTS verify_attempts;
        ALTER TABLE auth.otp_logs DROP COLUMN IF EXISTS otp_hash;
    """)
