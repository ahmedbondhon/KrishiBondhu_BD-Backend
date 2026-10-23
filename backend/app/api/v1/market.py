"""
api/v1/market.py
================
HTTP route handlers for HaatDor Market intelligence and produce group selling.
"""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.responses import success_response
from app.models.auth import User
from app.models.market import GroupSellingOffer, Market
from app.services.market_service import MarketService

router = APIRouter(prefix="/market", tags=["Market & HaatDor"])
market_service = MarketService()


class JoinOfferRequest(BaseModel):
    offered_quantity_kg: Decimal = Field(..., gt=0, description="Quantity in kg offered by farmer")
    plot_crop_id: Optional[UUID] = Field(None, description="Optional plot crop cycle reference")
    agreed_price_per_kg_bdt: Optional[Decimal] = Field(None, gt=0, description="Agreed price per kg")


@router.get("/markets", summary="List local markets and haats")
async def list_markets(
    division_id: Optional[UUID] = None,
    district_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Market).where(Market.is_active == True)
    if division_id:
        query = query.where(Market.division_id == division_id)
    if district_id:
        query = query.where(Market.district_id == district_id)
    result = await db.execute(query)
    markets = result.scalars().all()
    return success_response(
        data=[
            {
                "id": str(m.id),
                "name_en": m.name_en,
                "name_bn": m.name_bn,
                "market_type": m.market_type,
                "operating_days": m.operating_days,
            }
            for m in markets
        ],
        message="স্থানীয় বাজারের তালিকা সফলভাবে লোড হয়েছে।",
    )


@router.get("/offers", summary="List active group selling offers")
async def list_group_offers(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(GroupSellingOffer).where(GroupSellingOffer.is_deleted == False)
    if status_filter:
        query = query.where(GroupSellingOffer.status == status_filter)
    result = await db.execute(query)
    offers = result.scalars().all()
    return success_response(
        data=[
            {
                "id": str(o.id),
                "offer_code": o.offer_code,
                "crop_id": str(o.crop_id),
                "target_quantity_kg": float(o.target_quantity_kg),
                "current_aggregated_kg": float(o.current_aggregated_kg),
                "min_participant_quantity_kg": float(o.min_participant_quantity_kg),
                "expected_price_per_kg_bdt": float(o.expected_price_per_kg_bdt) if o.expected_price_per_kg_bdt else None,
                "status": o.status,
                "closing_date": o.closing_date.isoformat() if o.closing_date else None,
            }
            for o in offers
        ],
        message="গ্রুপ বিক্রির অফার তালিকা লোড হয়েছে।",
    )


@router.post("/offers/{offer_id}/join", status_code=status.HTTP_201_CREATED, summary="Join a group selling offer")
async def join_group_offer(
    offer_id: UUID,
    payload: JoinOfferRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    participant = await market_service.join_group_offer(
        db=db,
        offer_id=offer_id,
        farmer_id=current_user.id,
        offered_quantity_kg=payload.offered_quantity_kg,
        plot_crop_id=payload.plot_crop_id,
        agreed_price_per_kg_bdt=payload.agreed_price_per_kg_bdt,
    )
    return success_response(
        data={
            "id": str(participant.id),
            "offer_id": str(participant.offer_id),
            "offered_quantity_kg": float(participant.offered_quantity_kg),
            "status": participant.status,
        },
        message="গ্রুপ অফারে আপনার অংশগ্রহণ সফলভাবে রেকর্ড করা হয়েছে।",
    )

