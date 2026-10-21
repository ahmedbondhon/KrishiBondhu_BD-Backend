"""
schemas/farm.py
===============
Pydantic v2 schemas for farm and crop cycle endpoints.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ─────────────────────────────────────────────────────────
# Plot (Farm Land Parcel)
# ─────────────────────────────────────────────────────────

class CreatePlotRequest(BaseModel):
    """POST /api/v1/farms — Create a new farm plot."""
    name: str = Field(..., min_length=1, max_length=100, description="Plot name (e.g., 'উত্তর মাঠ')")
    area_bigha: Optional[Decimal] = Field(None, ge=0, description="Area in traditional bigha unit")
    area_sqm: Optional[Decimal] = Field(None, ge=0, description="Area in square meters")
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


class PlotCropResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    plot_id: UUID
    crop_id: UUID
    variety_id: Optional[UUID] = None
    current_stage_id: Optional[UUID] = None
    sowing_date: Optional[date] = None
    expected_harvest_date: Optional[date] = None
    status: str
    notes: Optional[str] = None
