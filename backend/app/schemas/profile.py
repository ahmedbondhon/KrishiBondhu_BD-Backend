# ============================================================================
# KrishiBondhu Bangladesh — Farmer Profile Schemas
# Request/Response DTOs for viewing, editing, and managing farmer profile
# ============================================================================

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class GeoName(BaseModel):
    """Geographic display names in Bangla and English (no raw UUIDs)."""

    model_config = ConfigDict(from_attributes=True)

    name_bn: str = Field(..., description="নাম (বাংলা)")
    name_en: str = Field(..., description="Name (English)")


class ProfileMeta(BaseModel):
    """Metadata containing raw geographic UUIDs for frontend dropdown selectors."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    division_id: uuid.UUID | None = None
    district_id: uuid.UUID | None = None
    upazila_id: uuid.UUID | None = None
    union_id: uuid.UUID | None = None
    divisionId: uuid.UUID | None = None
    districtId: uuid.UUID | None = None
    upazilaId: uuid.UUID | None = None
    unionId: uuid.UUID | None = None

    @model_validator(mode="before")
    @classmethod
    def sync_keys(cls, data):
        if isinstance(data, dict):
            div = data.get("division_id") or data.get("divisionId")
            dist = data.get("district_id") or data.get("districtId")
            upa = data.get("upazila_id") or data.get("upazilaId")
            uni = data.get("union_id") or data.get("unionId")
            return {
                "division_id": div,
                "district_id": dist,
                "upazila_id": upa,
                "union_id": uni,
                "divisionId": div,
                "districtId": dist,
                "upazilaId": upa,
                "unionId": uni,
            }
        return data


class ProfileResponse(BaseModel):
    """Farmer Profile display response without raw UUIDs in the main object."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: uuid.UUID
    full_name: str
    phone_number: str
    preferred_language: str
    avatar_url: str | None = None
    division: GeoName | None = None
    district: GeoName | None = None
    upazila: GeoName | None = None
    union: GeoName | None = None
    meta: ProfileMeta


class ProfileUpdateRequest(BaseModel):
    """DTO for editing farmer profile. Phone number is strictly immutable."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        populate_by_name=True,
        extra="forbid",
    )

    full_name: str | None = Field(
        default=None,
        alias="fullName",
        min_length=2,
        max_length=150,
        description="কৃষকের সম্পূর্ণ নাম",
    )
    preferred_language: Literal["bn", "en"] | None = Field(
        default=None,
        alias="preferredLanguage",
        description="পছন্দের ভাষা (bn / en)",
    )
    division_id: uuid.UUID | None = Field(
        default=None,
        alias="divisionId",
        description="সংশোধিত বিভাগের আইডি",
    )
    district_id: uuid.UUID | None = Field(
        default=None,
        alias="districtId",
        description="সংশোধিত জেলার আইডি",
    )
    upazila_id: uuid.UUID | None = Field(
        default=None,
        alias="upazilaId",
        description="সংশোধিত উপজেলার আইডি",
    )
    union_id: uuid.UUID | None = Field(
        default=None,
        alias="unionId",
        description="সংশোধিত ইউনিয়নের আইডি",
    )

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("নাম খালি রাখা যাবে না / Full name cannot be blank.")
        return value


class ProfileMutationResponse(BaseModel):
    """Standard mutation response returning a success message and updated data."""

    model_config = ConfigDict(populate_by_name=True)

    message: str
    profile: ProfileResponse
    data: ProfileResponse | None = None

    @model_validator(mode="after")
    def sync_data(self):
        if self.data is None:
            self.data = self.profile
        return self
