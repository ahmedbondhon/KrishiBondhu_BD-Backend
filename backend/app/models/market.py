"""
models/market.py
================
SQLAlchemy ORM models for the market schema:
  - market.group_selling_offers  → GroupSellingOffer
  - market.offer_participants    → OfferParticipant
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Market(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    market.markets — Local markets / haats registry table.
    """
    __tablename__ = "markets"
    __table_args__ = {"schema": "market"}

    name_en: Mapped[str] = mapped_column(String(150), nullable=False)
    name_bn: Mapped[str] = mapped_column(String(150), nullable=False)
    market_type: Mapped[str] = mapped_column(String(50), default="haat", nullable=False)
    division_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("geo.divisions.id", ondelete="SET NULL"))
    district_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("geo.districts.id", ondelete="SET NULL"))
    upazila_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("geo.upazilas.id", ondelete="SET NULL"))
    union_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("geo.unions.id", ondelete="SET NULL"))
    operating_days: Mapped[Optional[str]] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class GroupSellingOffer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    market.group_selling_offers — HaatDor produce aggregation offers.
    """
    __tablename__ = "group_selling_offers"
    __table_args__ = {"schema": "market"}

    offer_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    initiator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False
    )
    crop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("catalog.crops.id", ondelete="RESTRICT"), nullable=False
    )
    variety_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("catalog.crop_varieties.id", ondelete="SET NULL")
    )
    target_market_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("market.markets.id", ondelete="SET NULL")
    )
    union_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("geo.unions.id", ondelete="SET NULL")
    )

    target_quantity_kg: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    min_participant_quantity_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("50.00"))
    expected_price_per_kg_bdt: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    current_aggregated_kg: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False)
    closing_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    participants: Mapped[list["OfferParticipant"]] = relationship(
        "OfferParticipant", back_populates="offer", cascade="all, delete-orphan"
    )


class OfferParticipant(Base, UUIDPrimaryKeyMixin):
    """
    market.offer_participants — Farmer participation in aggregated group selling.
    """
    __tablename__ = "offer_participants"
    __table_args__ = {"schema": "market"}

    offer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("market.group_selling_offers.id", ondelete="CASCADE"), nullable=False
    )
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False
    )
    plot_crop_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farm.plot_crops.id", ondelete="SET NULL")
    )
    offered_quantity_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    agreed_price_per_kg_bdt: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(50), default="pledged", nullable=False)
    pledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )

    offer: Mapped["GroupSellingOffer"] = relationship("GroupSellingOffer", back_populates="participants")
