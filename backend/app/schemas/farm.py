"""
schemas/farm.py
===============
Pydantic v2 schemas for farm and crop cycle endpoints.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ─────────────────────────────────────────────────────────
# Plot (Farm Land Parcel)
# ─────────────────────────────────────────────────────────

class CreatePlotRequest(BaseModel):
    """POST /api/v1/farms — Create a new farm plot."""
    name: str = Field(..., min_length=1, max_length=100, description="Plot name (e.g., 'উত্তর মাঠ')")
    farmer_id: Optional[UUID] = Field(None, description="Target farmer ID if created on behalf by agent or admin")
    area_bigha: Optional[Decimal] = Field(None, gt=0, description="Area in traditional bigha unit")
    area_sqm: Optional[Decimal] = Field(None, gt=0, description="Area in square meters")
    soil_type: Optional[str] = Field(None, max_length=50)
    irrigation_source: Optional[str] = Field(None, max_length=50)
    division_id: Optional[UUID] = None
    district_id: Optional[UUID] = None
    upazila_id: Optional[UUID] = None
    union_id: Optional[UUID] = None

    @model_validator(mode="after")
    def validate_plot_area(self):
        if self.area_bigha is None and self.area_sqm is None:
            raise ValueError("জমির আয়তন (area_bigha অথবা area_sqm) উল্লেখ করা আবশ্যক এবং তা ০ এর বেশি হতে হবে।")
        return self


class UpdatePlotRequest(BaseModel):
    """PATCH/PUT /api/v1/farms/{plot_id} — Update farm plot details."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    area_bigha: Optional[Decimal] = Field(None, gt=0)
    area_sqm: Optional[Decimal] = Field(None, gt=0)
    soil_type: Optional[str] = Field(None, max_length=50)
    irrigation_source: Optional[str] = Field(None, max_length=50)
    division_id: Optional[UUID] = None
    district_id: Optional[UUID] = None
    upazila_id: Optional[UUID] = None
    union_id: Optional[UUID] = None


class PlotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    area_bigha: Optional[Decimal] = None
    area_sqm: Optional[Decimal] = None
    soil_type: Optional[str] = None
    irrigation_source: Optional[str] = None
    division_id: Optional[UUID] = None
    district_id: Optional[UUID] = None
    upazila_id: Optional[UUID] = None
    union_id: Optional[UUID] = None
    is_active: bool
    created_at: Optional[datetime] = None


# ─────────────────────────────────────────────────────────
# Crop Cycle (PlotCrop)
# ─────────────────────────────────────────────────────────

class CreatePlotCropRequest(BaseModel):
    """POST /api/v1/plots/{plot_id}/crop-cycles — Start a new crop cultivation cycle."""
    crop_id: UUID = Field(..., description="ID of the crop being planted")
    variety_id: Optional[UUID] = Field(None, description="Specific crop variety (optional)")
    current_stage_id: Optional[UUID] = Field(None, description="Current growth stage ID")
    sowing_date: Optional[date] = None
    expected_harvest_date: Optional[date] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_dates(self) -> "CreatePlotCropRequest":
        if self.sowing_date and self.expected_harvest_date:
            if self.expected_harvest_date < self.sowing_date:
                raise ValueError("সম্ভাব্য ফসল কাটার তারিখ বপনের তারিখের পূর্ববর্তী হতে পারে না।")
        return self


class UpdatePlotCropRequest(BaseModel):
    """PATCH /api/v1/farms/{plot_id}/crop-cycles/{cycle_id} — Update crop cycle status and yield."""
    current_stage_id: Optional[UUID] = Field(None, description="Current growth stage ID")
    expected_harvest_date: Optional[date] = None
    actual_harvest_date: Optional[date] = None
    status: Optional[Literal["planned", "active", "harvested", "failed"]] = Field(
        None, description="planned | active | harvested | failed"
    )
    yield_kg: Optional[Decimal] = Field(None, ge=0, description="Actual yield in kilograms")
    notes: Optional[str] = None


class PlotCropResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plot_id: UUID
    crop_id: UUID
    variety_id: Optional[UUID] = None
    current_stage_id: Optional[UUID] = None
    sowing_date: Optional[date] = None
    expected_harvest_date: Optional[date] = None
    actual_harvest_date: Optional[date] = None
    status: str
    yield_kg: Optional[Decimal] = None
    notes: Optional[str] = None
