"""
services/market_service.py
==========================
Market & HaatDor Group Selling Service.
Implements row-level locking (with_for_update) to prevent race conditions during produce aggregation.
"""

import uuid
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market import GroupSellingOffer, OfferParticipant


class MarketService:
    """Service handling Group Selling and Aggregation offers with race-condition prevention."""

    async def join_group_offer(
        self,
        db: AsyncSession,
        offer_id: uuid.UUID,
        farmer_id: uuid.UUID,
        offered_quantity_kg: Decimal,
        plot_crop_id: Optional[uuid.UUID] = None,
        agreed_price_per_kg_bdt: Optional[Decimal] = None,
    ) -> OfferParticipant:
        """
        Add a farmer to a group selling offer with row-level locking (with_for_update)
        to prevent race condition on `current_aggregated_kg` and status transitions.
        """
        # Lock the offer row exclusively for update
        stmt = (
            select(GroupSellingOffer)
            .where(
                GroupSellingOffer.id == offer_id,
                GroupSellingOffer.is_deleted == False,
            )
            .with_for_update()
        )
        result = await db.execute(stmt)
        offer = result.scalar_one_or_none()

        if not offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "OFFER_NOT_FOUND", "message_bn": "গ্রুপ বিক্রির অফারটি পাওয়া যায়নি।"},
            )

        if offer.status != "open":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "OFFER_NOT_OPEN", "message_bn": "এই অফারে নতুন অংশগ্রহণ গ্রহণ করা হচ্ছে না।"},
            )

        min_qty = offer.min_participant_quantity_kg or Decimal("0.00")
        if offered_quantity_kg < min_qty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "MIN_QUANTITY_NOT_MET",
                    "message_bn": f"নূন্যতম অংশগ্রহণের পরিমাণ {min_qty} কেজি হতে হবে।",
                },
            )

        # Check existing participation
        existing_part_res = await db.execute(
            select(OfferParticipant).where(
                OfferParticipant.offer_id == offer_id,
                OfferParticipant.farmer_id == farmer_id,
            )
        )
        if existing_part_res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "ALREADY_PARTICIPATING", "message_bn": "আপনি ইতিমধ্যে এই অফারে যুক্ত আছেন।"},
            )

        # Create participation record
        participant = OfferParticipant(
            offer_id=offer.id,
            farmer_id=farmer_id,
            plot_crop_id=plot_crop_id,
            offered_quantity_kg=offered_quantity_kg,
            agreed_price_per_kg_bdt=agreed_price_per_kg_bdt or offer.expected_price_per_kg_bdt,
            status="pledged",
        )
        db.add(participant)

        # Atomically increment current_aggregated_kg
        offer.current_aggregated_kg = (offer.current_aggregated_kg or Decimal("0.00")) + offered_quantity_kg
        if offer.current_aggregated_kg >= offer.target_quantity_kg:
            offer.status = "target_reached"

        await db.flush()
        return participant


market_service = MarketService()
