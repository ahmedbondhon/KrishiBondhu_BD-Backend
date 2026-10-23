"""
api/v1/catalog.py
=================
HTTP route handlers for agricultural catalog master data:
Crops, Crop Varieties, Growth Stages, and Crop Issues.

Routes:
  GET /api/v1/catalog/crops
  GET /api/v1/catalog/crops/{crop_id}
  GET /api/v1/catalog/crops/{crop_id}/varieties
  GET /api/v1/catalog/crops/{crop_id}/growth-stages
  GET /api/v1/catalog/crops/{crop_id}/issues
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_db
from app.core.responses import success_response
from app.models.catalog import Crop, CropVariety, GrowthStage, Issue

router = APIRouter(prefix="/catalog", tags=["Catalog"])


@router.get("/crops", summary="List all supported crops")
async def list_crops(
    db: AsyncSession = Depends(get_db),
):
    """Returns all active crops supported by the platform (e.g., Potato, Tomato, Chili)."""
    result = await db.execute(
        select(Crop).where(Crop.is_active == True).order_by(Crop.name_bn)
    )
    crops = result.scalars().all()

    return success_response(
        data=[
            {
                "id": str(c.id),
                "code": c.code,
                "name_en": c.name_en,
                "name_bn": c.name_bn,
                "scientific_name": c.scientific_name,
                "description": c.description,
                "icon_url": c.icon_url,
                "is_active": c.is_active,
            }
            for c in crops
        ],
        message=f"{len(crops)}টি ফসলের তথ্য পাওয়া গেছে।",
    )


async def _ensure_crop_exists(crop_id: UUID, db: AsyncSession) -> Crop:
    result = await db.execute(select(Crop).where(Crop.id == crop_id, Crop.is_active == True))
    crop = result.scalar_one_or_none()
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CROP_NOT_FOUND", "message_bn": "ফসলের তথ্য পাওয়া যায়নি।"},
        )
    return crop


@router.get("/crops/{crop_id}", summary="Get crop details with varieties and growth stages")
async def get_crop_details(
    crop_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Returns details for a specific crop including varieties and growth stages."""
    result = await db.execute(
        select(Crop)
        .options(
            selectinload(Crop.varieties.and_(CropVariety.is_active == True)),
            selectinload(Crop.growth_stages),
        )
        .where(Crop.id == crop_id, Crop.is_active == True)
    )
    crop = result.scalar_one_or_none()
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CROP_NOT_FOUND", "message_bn": "ফসলের তথ্য পাওয়া যায়নি।"},
        )

    # Sort growth stages by sequence_order
    sorted_stages = sorted(crop.growth_stages, key=lambda s: s.sequence_order)

    return success_response(
        data={
            "id": str(crop.id),
            "code": crop.code,
            "name_en": crop.name_en,
            "name_bn": crop.name_bn,
            "scientific_name": crop.scientific_name,
            "description": crop.description,
            "icon_url": crop.icon_url,
            "varieties": [
                {
                    "id": str(v.id),
                    "code": v.code,
                    "name_en": v.name_en,
                    "name_bn": v.name_bn,
                    "description": v.description,
                }
                for v in crop.varieties
                if v.is_active
            ],
            "growth_stages": [
                {
                    "id": str(s.id),
                    "stage_code": s.stage_code,
                    "name_en": s.name_en,
                    "name_bn": s.name_bn,
                    "sequence_order": s.sequence_order,
                    "description": s.description,
                }
                for s in sorted_stages
            ],
        },
        message="ফসলের বিস্তারিত তথ্য পাওয়া গেছে।",
    )


@router.get("/crops/{crop_id}/varieties", summary="List varieties for a specific crop")
async def list_crop_varieties(
    crop_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Returns all active varieties for a specific crop."""
    await _ensure_crop_exists(crop_id, db)
    result = await db.execute(
        select(CropVariety)
        .where(CropVariety.crop_id == crop_id, CropVariety.is_active == True)
        .order_by(CropVariety.name_bn)
    )
    varieties = result.scalars().all()

    return success_response(
        data=[
            {
                "id": str(v.id),
                "crop_id": str(v.crop_id),
                "code": v.code,
                "name_en": v.name_en,
                "name_bn": v.name_bn,
                "description": v.description,
            }
            for v in varieties
        ],
        message=f"{len(varieties)}টি জাতের তথ্য পাওয়া গেছে।",
    )


@router.get("/crops/{crop_id}/growth-stages", summary="List ordered growth stages for a crop")
async def list_growth_stages(
    crop_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Returns growth stages for a specific crop in sequential order."""
    await _ensure_crop_exists(crop_id, db)
    result = await db.execute(
        select(GrowthStage)
        .where(GrowthStage.crop_id == crop_id)
        .order_by(GrowthStage.sequence_order.asc())
    )
    stages = result.scalars().all()

    return success_response(
        data=[
            {
                "id": str(s.id),
                "crop_id": str(s.crop_id),
                "stage_code": s.stage_code,
                "name_en": s.name_en,
                "name_bn": s.name_bn,
                "sequence_order": s.sequence_order,
                "description": s.description,
            }
            for s in stages
        ],
        message=f"{len(stages)}টি বৃদ্ধির পর্যায় পাওয়া গেছে।",
    )


@router.get("/crops/{crop_id}/issues", summary="List common issues (diseases/pests) for a crop")
async def list_crop_issues(
    crop_id: UUID,
    category: Optional[str] = Query(None, description="Filter by category: disease | pest | deficiency | environmental"),
    db: AsyncSession = Depends(get_db),
):
    """Returns issues (diseases, pests, nutrient deficiencies) cataloged for a specific crop."""
    await _ensure_crop_exists(crop_id, db)
    query = select(Issue).where(Issue.crop_id == crop_id, Issue.is_active == True)
    if category:
        query = query.where(Issue.category == category)
    query = query.order_by(Issue.name_bn)

    result = await db.execute(query)
    issues = result.scalars().all()

    return success_response(
        data=[
            {
                "id": str(i.id),
                "crop_id": str(i.crop_id),
                "code": i.code,
                "name_en": i.name_en,
                "name_bn": i.name_bn,
                "category": i.category,
                "severity_level": i.severity_level,
                "scientific_name": i.scientific_name,
                "symptoms_bn": i.symptoms_bn,
            }
            for i in issues
        ],
        message=f"{len(issues)}টি রোগের/সমস্যার তথ্য পাওয়া গেছে।",
    )
