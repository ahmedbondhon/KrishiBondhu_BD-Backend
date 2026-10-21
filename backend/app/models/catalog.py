"""
models/catalog.py
=================
SQLAlchemy ORM models for the `catalog` schema.

Tables mapped here:
  - catalog.crops           → Crop
  - catalog.crop_varieties  → CropVariety
  - catalog.growth_stages   → GrowthStage
  - catalog.issues          → Issue
  - catalog.issue_growth_stages → IssueGrowthStage (many-to-many join)
  - catalog.remedies        → Remedy

The catalog is the master data for all agricultural knowledge:
what crops exist, what diseases they can get, and how to treat them.
"""

import uuid
from typing import List, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Crop(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    catalog.crops — Master list of supported crops.
    Seeded: Potato (আলু), Tomato (টমেটো), Chili (মরিচ).
    """
    __tablename__ = "crops"
    __table_args__ = {"schema": "catalog"}

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_bn: Mapped[str] = mapped_column(String(100), nullable=False)
    scientific_name: Mapped[Optional[str]] = mapped_column(String(150))
    description: Mapped[Optional[str]] = mapped_column(Text)
    icon_url: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    varieties: Mapped[List["CropVariety"]] = relationship("CropVariety", back_populates="crop")
    growth_stages: Mapped[List["GrowthStage"]] = relationship("GrowthStage", back_populates="crop")
    issues: Mapped[List["Issue"]] = relationship("Issue", back_populates="crop")


class CropVariety(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """catalog.crop_varieties — Named varieties/cultivars for each crop."""
    __tablename__ = "crop_varieties"
    __table_args__ = (
        UniqueConstraint("crop_id", "code", name="uq_crop_varieties_code"),
        {"schema": "catalog"},
    )

    crop_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("catalog.crops.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_bn: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    crop: Mapped["Crop"] = relationship("Crop", back_populates="varieties")


class GrowthStage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    catalog.growth_stages — Ordered growth stages for each crop
    (e.g., Seedling → Vegetative → Flowering → Fruiting → Harvest).
    """
    __tablename__ = "growth_stages"
    __table_args__ = (
        UniqueConstraint("crop_id", "sequence_order", name="uq_growth_stage_crop_order"),
        {"schema": "catalog"},
    )

    crop_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("catalog.crops.id", ondelete="CASCADE"), nullable=False)
    stage_code: Mapped[str] = mapped_column(String(50), nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_bn: Mapped[str] = mapped_column(String(100), nullable=False)
    sequence_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    crop: Mapped["Crop"] = relationship("Crop", back_populates="growth_stages")


class Issue(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    catalog.issues — Agricultural issues (diseases, pests, deficiencies) per crop.
    The AI model predicts the `code` of an Issue from a submitted image.
    """
    __tablename__ = "issues"
    __table_args__ = {"schema": "catalog"}

    crop_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("catalog.crops.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name_en: Mapped[str] = mapped_column(String(150), nullable=False)
    name_bn: Mapped[str] = mapped_column(String(150), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # disease | pest | deficiency | environmental
    scientific_name: Mapped[Optional[str]] = mapped_column(String(150))
    symptoms_bn: Mapped[Optional[str]] = mapped_column(Text)
    symptoms_en: Mapped[Optional[str]] = mapped_column(Text)
    severity_level: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    crop: Mapped["Crop"] = relationship("Crop", back_populates="issues")
    remedies: Mapped[List["Remedy"]] = relationship("Remedy", back_populates="issue")


class Remedy(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    catalog.remedies — Treatment guidelines for a specific Issue.
    Supports chemical, organic, cultural, and preventive remedy types.
    """
    __tablename__ = "remedies"
    __table_args__ = {"schema": "catalog"}

    issue_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("catalog.issues.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # chemical | organic | cultural | preventive
    title_bn: Mapped[str] = mapped_column(String(255), nullable=False)
    title_en: Mapped[Optional[str]] = mapped_column(String(255))
    description_bn: Mapped[str] = mapped_column(Text, nullable=False)
    description_en: Mapped[Optional[str]] = mapped_column(Text)
    chemical_name: Mapped[Optional[str]] = mapped_column(String(150))
    dosage_bn: Mapped[Optional[str]] = mapped_column(Text)
    safety_instructions_bn: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    issue: Mapped["Issue"] = relationship("Issue", back_populates="remedies")
