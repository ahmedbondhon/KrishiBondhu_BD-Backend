"""Add auth module tables: refresh_tokens, login_attempts, and extended user columns

Revision ID: 001_auth_module
Revises: None
Create Date: 2026-10-09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers
revision: str = "001_auth_module"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure auth schema exists
    op.execute("CREATE SCHEMA IF NOT EXISTS auth")

    # ------------------------------------------------------------------
    # Add new columns to auth.users (extending the existing table)
    # These columns are added IF NOT EXISTS to be safe with existing DBs
    # ------------------------------------------------------------------
    op.execute("""
        DO $$
        BEGIN
            -- status column (replaces simple is_active boolean for richer state)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'auth' AND table_name = 'users' AND column_name = 'status'
            ) THEN
                ALTER TABLE auth.users
                ADD COLUMN status VARCHAR(30) DEFAULT 'active' NOT NULL
                CHECK (status IN ('active','inactive','pending_approval','suspended','deleted'));
            END IF;

            -- email column
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'auth' AND table_name = 'users' AND column_name = 'email'
            ) THEN
                ALTER TABLE auth.users ADD COLUMN email VARCHAR(255) UNIQUE;
            END IF;

            -- phone_verified
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'auth' AND table_name = 'users' AND column_name = 'phone_verified'
            ) THEN
                ALTER TABLE auth.users ADD COLUMN phone_verified BOOLEAN DEFAULT FALSE NOT NULL;
            END IF;

            -- email_verified
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'auth' AND table_name = 'users' AND column_name = 'email_verified'
            ) THEN
                ALTER TABLE auth.users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE NOT NULL;
            END IF;

            -- last_login_at
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'auth' AND table_name = 'users' AND column_name = 'last_login_at'
            ) THEN
                ALTER TABLE auth.users ADD COLUMN last_login_at TIMESTAMPTZ;
            END IF;
        END
        $$;
    """)

    # ------------------------------------------------------------------
    # auth.refresh_tokens — one-use rotating refresh tokens
    # ------------------------------------------------------------------
    op.create_table(
        "refresh_tokens",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(512), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        schema="auth",
    )
    op.create_index("idx_auth_refresh_tokens_user_id", "refresh_tokens", ["user_id"], schema="auth")
    op.create_index("idx_auth_refresh_tokens_hash", "refresh_tokens", ["token_hash"], schema="auth")

    # ------------------------------------------------------------------
    # auth.login_attempts — brute-force protection
    # ------------------------------------------------------------------
    op.create_table(
        "login_attempts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("success", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        schema="auth",
    )
    op.create_index("idx_auth_login_attempts_user_id", "login_attempts", ["user_id"], schema="auth")
    op.create_index(
        "idx_auth_login_attempts_user_time",
        "login_attempts",
        ["user_id", "attempted_at"],
        schema="auth",
    )

    # ------------------------------------------------------------------
    # Add 'technical_admin' to roles seed if not present
    # ------------------------------------------------------------------
    op.execute("""
        INSERT INTO auth.roles (id, code, name, description)
        VALUES (
            '11000000-0000-0000-0000-000000000005',
            'technical_admin',
            'Technical Administrator',
            'Developer/ML administrator managing models, deployments, and technical infrastructure'
        )
        ON CONFLICT (code) DO UPDATE SET
            name = EXCLUDED.name,
            description = EXCLUDED.description;
    """)


def downgrade() -> None:
    op.drop_table("login_attempts", schema="auth")
    op.drop_table("refresh_tokens", schema="auth")

    # Remove added columns (reverse order)
    op.execute("ALTER TABLE auth.users DROP COLUMN IF EXISTS last_login_at")
    op.execute("ALTER TABLE auth.users DROP COLUMN IF EXISTS email_verified")
    op.execute("ALTER TABLE auth.users DROP COLUMN IF EXISTS phone_verified")
    op.execute("ALTER TABLE auth.users DROP COLUMN IF EXISTS email")
    op.execute("ALTER TABLE auth.users DROP COLUMN IF EXISTS status")

    # Remove technical_admin role
    op.execute("DELETE FROM auth.roles WHERE code = 'technical_admin'")
