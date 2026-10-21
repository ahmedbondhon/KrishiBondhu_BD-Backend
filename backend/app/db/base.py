"""
db/base.py
==========
SQLAlchemy declarative base class and shared column mixins.

All ORM models in this project inherit from `Base`. This file also
provides `TimestampMixin` for tables that track created_at/updated_at.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedColumn, mapped_column


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.

    Using SQLAlchemy 2.0 style `DeclarativeBase`. All models that inherit
    from this class are registered and available to Alembic for migrations.
    """
    pass


class UUIDPrimaryKeyMixin:
    """
    Mixin that adds a UUIDv4 primary key column named `id`.
    Matches the database convention: `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`.
    """
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )


class TimestampMixin:
    """
    Mixin that adds `created_at` and `updated_at` TIMESTAMPTZ columns.
    - created_at: Set once on INSERT using the DB server clock.
    - updated_at: Updated on every UPDATE using the DB server clock.
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


