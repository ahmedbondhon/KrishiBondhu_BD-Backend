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

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.responses import success_response
from app.models.geo import District, Division, Union, Upazila

router = APIRouter(prefix="/geo", tags=["Geographic Hierarchy"])


@router.get("/divisions", summary="List all administrative divisions")
async def list_divisions(
    db: AsyncSession = Depends(get_db),
):
    """Returns all active divisions in Bangladesh (e.g. Rajshahi, Khulna, Dhaka)."""
    result = await db.execute(
        select(Division).where(Division.is_active == True).order_by(Division.name_bn)
    )
    divisions = result.scalars().all()

    return success_response(
        data=[
            {
                "id": str(d.id),
                "bbs_code": d.bbs_code,
                "name_en": d.name_en,
                "name_bn": d.name_bn,
            }
            for d in divisions
        ],
        message=f"{len(divisions)}টি বিভাগের তথ্য পাওয়া গেছে।",
    )


@router.get("/districts", summary="List districts (optionally filtered by division)")
async def list_districts(
    division_id: Optional[UUID] = Query(None, description="Filter districts by division ID"),
    db: AsyncSession = Depends(get_db),
):
    """Returns districts, optionally filtered by division ID."""
    query = select(District).where(District.is_active == True)
    if division_id:
        query = query.where(District.division_id == division_id)
    query = query.order_by(District.name_bn)

    result = await db.execute(query)
    districts = result.scalars().all()

    return success_response(
        data=[
            {
                "id": str(d.id),
                "division_id": str(d.division_id),
                "bbs_code": d.bbs_code,
                "name_en": d.name_en,
                "name_bn": d.name_bn,
            }
            for d in districts
        ],
        message=f"{len(districts)}টি জেলার তথ্য পাওয়া গেছে।",
    )


@router.get("/upazilas", summary="List upazilas (optionally filtered by district)")
async def list_upazilas(
    district_id: Optional[UUID] = Query(None, description="Filter upazilas by district ID"),
    db: AsyncSession = Depends(get_db),
):
    """Returns upazilas, optionally filtered by district ID."""
    query = select(Upazila).where(Upazila.is_active == True)
    if district_id:
        query = query.where(Upazila.district_id == district_id)
    query = query.order_by(Upazila.name_bn)

    result = await db.execute(query)
    upazilas = result.scalars().all()

    return success_response(
        data=[
            {
                "id": str(u.id),
                "district_id": str(u.district_id),
                "bbs_code": u.bbs_code,
                "name_en": u.name_en,
                "name_bn": u.name_bn,
            }
            for u in upazilas
        ],
        message=f"{len(upazilas)}টি উপজেলার তথ্য পাওয়া গেছে।",
    )


@router.get("/unions", summary="List unions (optionally filtered by upazila)")
async def list_unions(
    upazila_id: Optional[UUID] = Query(None, description="Filter unions by upazila ID"),
    db: AsyncSession = Depends(get_db),
):
    """Returns unions, optionally filtered by upazila ID."""
    query = select(Union).where(Union.is_active == True)
    if upazila_id:
        query = query.where(Union.upazila_id == upazila_id)
    query = query.order_by(Union.name_bn)

    result = await db.execute(query)
    unions = result.scalars().all()

    return success_response(
        data=[
            {
                "id": str(u.id),
                "upazila_id": str(u.upazila_id),
                "bbs_code": u.bbs_code,
                "name_en": u.name_en,
                "name_bn": u.name_bn,
            }
            for u in unions
        ],
        message=f"{len(unions)}টি ইউনিয়নের তথ্য পাওয়া গেছে।",
    )
