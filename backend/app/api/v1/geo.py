"""
api/v1/geo.py
=============
HTTP route handlers for geographic master data:
Divisions, Districts, Upazilas, and Unions.

Routes:
  GET /api/v1/geo/divisions
  GET /api/v1/geo/districts?division_id=...
  GET /api/v1/geo/upazilas?district_id=...
  GET /api/v1/geo/unions?upazila_id=...
"""

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.repositories.auth import AuthRepository

router = APIRouter(prefix="/geo", tags=["Geographic Hierarchy"])


def _format_geo(item: Any, extra_fields: list[str] | None = None) -> dict:
    if isinstance(item, dict):
        return item
    data = {
        "id": str(item.id),
        "bbs_code": item.bbs_code,
        "name_en": item.name_en,
        "name_bn": item.name_bn,
    }
    if extra_fields:
        for f in extra_fields:
            if hasattr(item, f):
                val = getattr(item, f)
                data[f] = str(val) if val is not None else None
    return data


@router.get("/divisions", summary="List all administrative divisions")
async def list_divisions(
    db: AsyncSession = Depends(get_db),
):
    """Returns all active divisions in Bangladesh (e.g. Rajshahi, Khulna, Dhaka)."""
    repo = AuthRepository(db)
    divisions = await repo.get_divisions()
    return [_format_geo(d) for d in divisions]


@router.get("/districts", summary="List districts (optionally filtered by division)")
async def list_districts(
    division_id: Optional[UUID] = Query(None, description="Filter districts by division ID"),
    db: AsyncSession = Depends(get_db),
):
    """Returns districts, optionally filtered by division ID."""
    repo = AuthRepository(db)
    districts = await repo.get_districts(division_id=division_id)
    return [_format_geo(d, ["division_id"]) for d in districts]


@router.get("/upazilas", summary="List upazilas (optionally filtered by district)")
async def list_upazilas(
    district_id: Optional[UUID] = Query(None, description="Filter upazilas by district ID"),
    db: AsyncSession = Depends(get_db),
):
    """Returns upazilas, optionally filtered by district ID."""
    repo = AuthRepository(db)
    upazilas = await repo.get_upazilas(district_id=district_id)
    return [_format_geo(u, ["district_id"]) for u in upazilas]


@router.get("/unions", summary="List unions (optionally filtered by upazila)")
async def list_unions(
    upazila_id: Optional[UUID] = Query(None, description="Filter unions by upazila ID"),
    db: AsyncSession = Depends(get_db),
):
    """Returns unions, optionally filtered by upazila ID."""
    repo = AuthRepository(db)
    unions = await repo.get_unions(upazila_id=upazila_id)
    return [_format_geo(u, ["upazila_id"]) for u in unions]
