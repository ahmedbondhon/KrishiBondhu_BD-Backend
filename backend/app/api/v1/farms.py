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

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_roles
from app.core.responses import success_response
from app.models.auth import User
from app.models.farm import Plot, PlotCrop
from app.schemas.farm import CreatePlotCropRequest, CreatePlotRequest, PlotCropResponse, PlotResponse

router = APIRouter(prefix="/farms", tags=["Farms & Crop Cycles"])


@router.post("", status_code=201, summary="Create a new farm plot")
async def create_farm(
    payload: CreatePlotRequest,
    current_user: User = Depends(require_roles("farmer", "agent", "admin")),
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new land plot owned by the current farmer.
    Area can be in bigha (traditional Bangladesh unit) or square meters.
    """
    plot = Plot(
        user_id=current_user.id,
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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns all non-deleted plots owned by the authenticated farmer."""
    result = await db.execute(
        select(Plot).where(
            Plot.user_id == current_user.id,
            Plot.is_deleted == False,
        ).order_by(Plot.created_at.desc())
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
    The crop, variety, and current growth stage are all optional at creation.
    """
    # Verify plot ownership
    result = await db.execute(
        select(Plot).where(
            Plot.id == plot_id,
            Plot.user_id == current_user.id,
            Plot.is_deleted == False,
        )
    )
    plot = result.scalar_one_or_none()
    if not plot:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PLOT_NOT_FOUND", "message_bn": "জমিটি পাওয়া যায়নি।"},
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

    if current_user.role_code not in ("admin", "administrator", "tech_admin", "technical_admin") and plot.user_id != current_user.id:
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
