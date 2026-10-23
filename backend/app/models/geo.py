"""
models/geo.py
=============
SQLAlchemy ORM models for the administrative geographic hierarchy (schema: geo).

Tables mapped:
  - geo.divisions → Division
  - geo.districts → District
  - geo.upazilas  → Upazila
  - geo.unions    → Union
"""

import uuid
from typing import List, Optional

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Division(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """geo.divisions — Top-level administrative divisions in Bangladesh."""
    __tablename__ = "divisions"
    __table_args__ = {"schema": "geo"}

    bbs_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_bn: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    districts: Mapped[List["District"]] = relationship("District", back_populates="division")


class District(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """geo.districts — Districts within a division."""
    __tablename__ = "districts"
    __table_args__ = {"schema": "geo"}

    division_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("geo.divisions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    bbs_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_bn: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    division: Mapped["Division"] = relationship("Division", back_populates="districts")
    upazilas: Mapped[List["Upazila"]] = relationship("Upazila", back_populates="district")


class Upazila(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """geo.upazilas — Sub-districts (Upazilas) within a district."""
    __tablename__ = "upazilas"
    __table_args__ = {"schema": "geo"}

    district_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("geo.districts.id", ondelete="RESTRICT"),
        nullable=False,
    )
    bbs_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_bn: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    district: Mapped["District"] = relationship("District", back_populates="upazilas")
    unions: Mapped[List["Union"]] = relationship("Union", back_populates="upazila")


class Union(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """geo.unions — Rural administrative councils (Unions) within an upazila."""
    __tablename__ = "unions"
    __table_args__ = {"schema": "geo"}

    upazila_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("geo.upazilas.id", ondelete="RESTRICT"),
        nullable=False,
    )
    bbs_code: Mapped[str] = mapped_column(String(10), nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_bn: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    upazila: Mapped["Upazila"] = relationship("Upazila", back_populates="unions")
