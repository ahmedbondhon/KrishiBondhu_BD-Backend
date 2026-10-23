# ============================================================================
# KrishiBondhu Bangladesh — Farmer Profile Routes (v1)
# Clean and minimal HTTP endpoints for profile view, edit, and avatar actions
# ============================================================================

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.controllers.profile import ProfileController
from app.db.session import get_db
from app.schemas.profile import (
    ProfileMutationResponse,
    ProfileResponse,
    ProfileUpdateRequest,
)
from app.services.profile import ProfileService

router = APIRouter(prefix="/farmer/profile", tags=["Farmer Profile"])


def get_profile_service(db: Annotated[AsyncSession, Depends(get_db)]) -> ProfileService:
    return ProfileService(db)


ProfileServiceDep = Annotated[ProfileService, Depends(get_profile_service)]


@router.get(
    "",
    response_model=ProfileResponse,
    summary="কৃষক প্রোফাইল তথ্য প্রদর্শন (View Profile)",
)
async def get_profile(
    current_user: CurrentUser,
    service: ProfileServiceDep,
):
    return await ProfileController.get_profile(current_user, service)


@router.put(
    "",
    response_model=ProfileMutationResponse,
    summary="কৃষক প্রোফাইল তথ্য পরিবর্তন (Edit Profile)",
)
async def update_profile(
    payload: ProfileUpdateRequest,
    current_user: CurrentUser,
    service: ProfileServiceDep,
):
    return await ProfileController.update_profile(current_user, payload, service)


@router.post(
    "/avatar",
    response_model=ProfileMutationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="প্রোফাইল ছবি আপলোড (Upload Avatar)",
)
async def upload_avatar(
    current_user: CurrentUser,
    service: ProfileServiceDep,
    file: UploadFile = File(..., description="প্রোফাইল ইমেজ ফাইল (JPEG/PNG/WebP, সর্বোচ্চ ২MB)"),
):
    return await ProfileController.upload_avatar(current_user, file, service)


@router.delete(
    "/avatar",
    summary="প্রোফাইল ছবি মুছে ফেলা (Delete Avatar)",
)
async def delete_avatar(
    current_user: CurrentUser,
    service: ProfileServiceDep,
):
    return await ProfileController.delete_avatar(current_user, service)
