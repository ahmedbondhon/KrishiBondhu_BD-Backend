"""
models/farm.py
==============
SQLAlchemy ORM models for the `farm` schema.

Tables mapped here:
  - farm.plots      → Plot   (a farmer's land parcel)
  - farm.plot_crops → PlotCrop (an active crop cultivation cycle on a plot)

Each farmer can own multiple Plots.
Each Plot can have multiple PlotCrops (cultivation cycles) over time,
but typically one active cycle at a time.

Note on PostGIS geometry columns:
  The `location` and `boundary` columns store PostGIS geometry types.
  We store lat/lng as simple Numeric fields alongside for non-GIS queries.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Plot(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    farm.plots — A physical land parcel owned by a farmer.

    Identified by the farmer's user_id. Area can be expressed in
    Bengali 'bigha' units (traditional) or square meters (metric).
    """
    __tablename__ = "plots"
    __table_args__ = {"schema": "farm"}

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    area_bigha: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    area_sqm: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    soil_type: Mapped[Optional[str]] = mapped_column(String(50))
    irrigation_source: Mapped[Optional[str]] = mapped_column(String(50))

    # Geographic FKs (administrative hierarchy)
    # Note: DB-level FK constraints exist in SQL migrations; no ORM geo models needed.
    division_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    district_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    upazila_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    union_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    # Soft delete support
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    crop_cycles: Mapped[list["PlotCrop"]] = relationship("PlotCrop", back_populates="plot")


class PlotCrop(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    farm.plot_crops — An active (or past) crop cultivation cycle on a plot.

    Status lifecycle: planned → active → harvested | failed
    The `current_stage_id` is updated as the crop grows through growth stages.
    """
    __tablename__ = "plot_crops"
    __table_args__ = {"schema": "farm"}

    plot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("farm.plots.id", ondelete="CASCADE"), nullable=False)
    crop_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("catalog.crops.id", ondelete="RESTRICT"), nullable=False)
    variety_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("catalog.crop_varieties.id", ondelete="SET NULL"))
    current_stage_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("catalog.growth_stages.id", ondelete="SET NULL"))

    sowing_date: Mapped[Optional[date]] = mapped_column(Date)
    expected_harvest_date: Mapped[Optional[date]] = mapped_column(Date)
    actual_harvest_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    yield_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    plot: Mapped["Plot"] = relationship("Plot", back_populates="crop_cycles")
