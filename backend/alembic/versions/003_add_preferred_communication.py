"""Add preferred_communication to auth.users

Revision ID: 003_add_preferred_communication
Revises: 002_otp_security_and_audit
Create Date: 2026-10-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003_add_preferred_communication"
down_revision: Union[str, None] = "002_otp_security_and_audit"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'auth' AND table_name = 'users' AND column_name = 'preferred_communication'
            ) THEN
                ALTER TABLE auth.users ADD COLUMN preferred_communication VARCHAR(20) DEFAULT 'sms' NOT NULL;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'auth' AND table_name = 'users' AND column_name = 'preferred_communication'
            ) THEN
                ALTER TABLE auth.users DROP COLUMN preferred_communication;
            END IF;
        END $$;
    """)
