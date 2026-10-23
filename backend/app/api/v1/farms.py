"""
api/v1/farms.py
===============
HTTP route handlers for farm plot and crop cycle management.

Routes:
  POST /api/v1/farms                           → Create a farm plot
  GET  /api/v1/farms                           → List current farmer's plots
  POST /api/v1/farms/{plot_id}/crop-cycles     → Start a crop cycle on a plot
  GET  /api/v1/farms/{plot_id}/crop-cycles     → List crop cycles for a plot

All routes require authentication (JWT Bearer token).
Only the plot owner can access their own plots (enforced in service layer).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_roles
from app.core.responses import success_response
from app.models.auth import User
from app.models.catalog import Crop, CropVariety, GrowthStage
from app.models.farm import Plot, PlotCrop
from app.models.geo import District, Division, Union, Upazila
from app.schemas.farm import CreatePlotCropRequest, CreatePlotRequest, PlotCropResponse, PlotResponse

router = APIRouter(prefix="/farms", tags=["Farms & Crop Cycles"])


@router.post("", status_code=201, summary="Create a new farm plot")
async def create_farm(
    payload: CreatePlotRequest,
    current_user: User = Depends(require_roles("farmer", "agent", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new land plot owned by the current farmer (or created on behalf by agent/admin).
    Area can be in bigha (traditional Bangladesh unit) or square meters.
    """
    target_user_id = current_user.id
    user_role = getattr(current_user, "role_code", "") or (current_user.role.code if current_user.role else "")
    if user_role in ("agent", "admin", "administrator", "tech_admin", "technical_admin") and payload.farmer_id:
        target_user_id = payload.farmer_id

    # Geographic hierarchy validation (Bug 1.3)
    if payload.division_id:
        div = await db.scalar(select(Division.id).where(Division.id == payload.division_id, Division.is_active == True))
        if not div:
            raise HTTPException(status_code=400, detail={"code": "INVALID_GEO", "message_bn": "বিভাগটি খুঁজে পাওয়া যায়নি।"})

    if payload.district_id:
        dist_stmt = select(District.id).where(District.id == payload.district_id, District.is_active == True)
        if payload.division_id:
            dist_stmt = dist_stmt.where(District.division_id == payload.division_id)
        dist = await db.scalar(dist_stmt)
        if not dist:
            raise HTTPException(status_code=400, detail={"code": "INVALID_GEO", "message_bn": "জেলাটি নির্বাচিত বিভাগের আওতাভুক্ত নয়।"})

    if payload.upazila_id:
        upz_stmt = select(Upazila.id).where(Upazila.id == payload.upazila_id, Upazila.is_active == True)
        if payload.district_id:
            upz_stmt = upz_stmt.where(Upazila.district_id == payload.district_id)
        upz = await db.scalar(upz_stmt)
        if not upz:
            raise HTTPException(status_code=400, detail={"code": "INVALID_GEO", "message_bn": "উপজেলাটি নির্বাচিত জেলার আওতাভুক্ত নয়।"})

    if payload.union_id:
        union_stmt = select(Union.id).where(Union.id == payload.union_id, Union.is_active == True)
        if payload.upazila_id:
            union_stmt = union_stmt.where(Union.upazila_id == payload.upazila_id)
        un = await db.scalar(union_stmt)
        if not un:
            raise HTTPException(status_code=400, detail={"code": "INVALID_GEO", "message_bn": "ইউনিয়নটি নির্বাচিত উপজেলার আওতাভুক্ত নয়।"})

    plot = Plot(
        user_id=target_user_id,
        name=payload.name,
        area_bigha=payload.area_bigha,
        area_sqm=payload.area_sqm,
        soil_type=payload.soil_type,
        irrigation_source=payload.irrigation_source,
        division_id=payload.division_id,
        district_id=payload.district_id,
        upazila_id=payload.upazila_id,
        union_id=payload.union_id,
    )
    db.add(plot)
    await db.flush()

    return success_response(
        data=PlotResponse.model_validate(plot).model_dump(),
        message="জমি সফলভাবে নিবন্ধিত হয়েছে।",
        status_code=201,
    )


@router.get("", summary="List all farm plots for the current farmer")
async def list_farms(
    limit: int = Query(50, ge=1, le=200, description="Max plots to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    **kwargs,
):
    """Returns all non-deleted plots owned by the authenticated farmer."""
    result = await db.execute(
        select(Plot).where(
            Plot.user_id == current_user.id,
            Plot.is_deleted == False,
        ).order_by(Plot.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    plots = result.scalars().all()

    return success_response(
        data=[PlotResponse.model_validate(p).model_dump() for p in plots],
        message=f"{len(plots)}টি জমি পাওয়া গেছে।",
    )


@router.post("/{plot_id}/crop-cycles", status_code=201, summary="Start a crop cycle on a plot")
async def create_crop_cycle(
    plot_id: UUID,
    payload: CreatePlotCropRequest,
    current_user: User = Depends(require_roles("farmer", "agent", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """
    Assign a crop cultivation cycle to a plot.
    Validates crop_id, variety_id, and current_stage_id relationships.
    """
    # Verify plot ownership / access
    plot_stmt = select(Plot).where(Plot.id == plot_id, Plot.is_deleted == False)
    user_role = getattr(current_user, "role_code", "") or (current_user.role.code if current_user.role else "")
    if user_role not in ("admin", "administrator", "tech_admin", "technical_admin", "agent"):
        plot_stmt = plot_stmt.where(Plot.user_id == current_user.id)
    result = await db.execute(plot_stmt)
    plot = result.scalar_one_or_none()
    if not plot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PLOT_NOT_FOUND", "message_bn": "জমিটি পাওয়া যায়নি।"},
        )

    # Verify crop exists (Bug 1.3)
    crop = await db.scalar(select(Crop.id).where(Crop.id == payload.crop_id, Crop.is_active == True))
    if not crop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CROP_NOT_FOUND", "message_bn": "ফসলটি পাওয়া যায়নি।"},
        )

    # Verify variety belongs to crop (Bug 1.3)
    if payload.variety_id:
        variety = await db.scalar(
            select(CropVariety.id).where(
                CropVariety.id == payload.variety_id,
                CropVariety.crop_id == payload.crop_id,
            )
        )
        if not variety:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_VARIETY", "message_bn": "জাতটি নির্বাচিত ফসলের সাথে মেলে না।"},
            )

    # Verify growth stage belongs to crop (Bug 1.3)
    if payload.current_stage_id:
        stage = await db.scalar(
            select(GrowthStage.id).where(
                GrowthStage.id == payload.current_stage_id,
                GrowthStage.crop_id == payload.crop_id,
            )
        )
        if not stage:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_GROWTH_STAGE", "message_bn": "বৃদ্ধির পর্যায়টি নির্বাচিত ফসলের সাথে মেলে না।"},
            )

    crop_cycle = PlotCrop(
        plot_id=plot.id,
        crop_id=payload.crop_id,
        variety_id=payload.variety_id,
        current_stage_id=payload.current_stage_id,
        sowing_date=payload.sowing_date,
        expected_harvest_date=payload.expected_harvest_date,
        notes=payload.notes,
        status="active",
    )
    db.add(crop_cycle)
    await db.flush()

    return success_response(
        data=PlotCropResponse.model_validate(crop_cycle).model_dump(),
        message="ফসল চক্র শুরু হয়েছে।",
        status_code=201,
    )


@router.get("/{plot_id}/crop-cycles", summary="List crop cycles for a plot")
async def list_crop_cycles(
    plot_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all active and past crop cycles for a specific plot."""
    # Verify plot ownership / access
    plot_result = await db.execute(
        select(Plot).where(
            Plot.id == plot_id,
            Plot.is_deleted == False,
        )
    )
    plot = plot_result.scalar_one_or_none()
    if not plot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PLOT_NOT_FOUND", "message_bn": "জমিটি পাওয়া যায়নি।"},
        )

    user_role = getattr(current_user, "role_code", "") or (current_user.role.code if getattr(current_user, "role", None) else "")
    if user_role not in ("admin", "administrator", "tech_admin", "technical_admin", "agent") and plot.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message_bn": "আপনার এই জমির তথ্য দেখার অনুমতি নেই।"},
        )

    result = await db.execute(
        select(PlotCrop).where(
            PlotCrop.plot_id == plot_id,
            PlotCrop.is_deleted == False,
        ).order_by(PlotCrop.created_at.desc())
    )
    cycles = result.scalars().all()

    return success_response(
        data=[PlotCropResponse.model_validate(c).model_dump() for c in cycles],
        message=f"{len(cycles)}টি ফসল চক্র পাওয়া গেছে।",
    )
