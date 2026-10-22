# ============================================================================
# KrishiBondhu Bangladesh — Farmer Profile Controller
# Handles profile presentation, updates, and avatar media actions
# ============================================================================

from fastapi import UploadFile

from app.models.auth import User
from app.schemas.profile import ProfileMutationResponse, ProfileResponse, ProfileUpdateRequest
from app.services.profile import ProfileService


class ProfileController:
    """Controller mediating between Farmer Profile HTTP endpoints and ProfileService."""

    @staticmethod
    async def get_profile(user: User, service: ProfileService) -> ProfileResponse:
        """Display farmer registration profile data."""
        return await service.get_profile(user)

    @staticmethod
    async def update_profile(
        user: User, payload: ProfileUpdateRequest, service: ProfileService
    ) -> ProfileMutationResponse:
        """Process farmer profile update and return localized success message with updated data."""
        updated_profile = await service.update_profile(user, payload)
        return ProfileMutationResponse(
            message="প্রোফাইল সফলভাবে আপডেট করা হয়েছে / Profile updated successfully.",
            profile=updated_profile,
        )

    @staticmethod
    async def upload_avatar(
        user: User, file: UploadFile, service: ProfileService
    ) -> ProfileMutationResponse:
        """Process avatar picture upload and return updated profile."""
        updated_profile = await service.upload_avatar(user, file)
        return ProfileMutationResponse(
            message="প্রোফাইল ছবি সফলভাবে আপলোড করা হয়েছে / Profile picture uploaded successfully.",
            profile=updated_profile,
        )

    @staticmethod
    async def delete_avatar(user: User, service: ProfileService) -> dict[str, str]:
        """Remove farmer profile avatar picture."""
        await service.delete_avatar(user)
        return {"message": "প্রোফাইল ছবি সফলভাবে মুছে ফেলা হয়েছে / Profile picture deleted successfully."}
