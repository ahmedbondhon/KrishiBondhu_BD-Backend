# ============================================================================
# KrishiBondhu Bangladesh — Profile Service
# Business logic for farmer profile view, edit, geo checks, and avatar handling
# ============================================================================

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import InvalidProfileDataError, UserNotFoundError
from app.models.auth import User
from app.models.geo import District, Division, Union, Upazila
from app.repositories.profile import ProfileRepository
from app.schemas.profile import GeoName, ProfileMeta, ProfileResponse
from app.services.supabase_client import supabase_client

settings = get_settings()

MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2MB
ALLOWED_AVATAR_TYPES = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class ProfileService:
    """Service handling farmer profile data display, dynamic edits, and avatar uploads."""

    def __init__(self, db: AsyncSession):
        self.repo = ProfileRepository(db)

    @staticmethod
    def _format_profile(row) -> ProfileResponse:
        user, division, district, upazila, union = row

        def make_geo(entity) -> GeoName | None:
            return GeoName(name_bn=entity.name_bn, name_en=entity.name_en) if entity else None

        avatar_url = user.avatar_url
        if avatar_url and not avatar_url.startswith(("http://", "https://")):
            clean_path = avatar_url.lstrip("/")
            # Ensure static mount path prefix (/static/) is included for relative avatar paths
            if clean_path.startswith("avatars/"):
                clean_path = f"static/{clean_path}"
            elif clean_path.startswith("uploads/"):
                # upload_dir is mounted at /static and /uploads
                clean_path = f"static/{clean_path[8:]}" if clean_path[8:].startswith("avatars/") else f"static/{clean_path}"
            elif not clean_path.startswith("static/"):
                clean_path = f"static/{clean_path}"
            avatar_url = f"{settings.public_base_url.rstrip('/')}/{clean_path}"

        return ProfileResponse(
            id=user.id,
            full_name=user.full_name,
            phone_number=user.phone_number,
            preferred_language=user.preferred_language,
            avatar_url=avatar_url,
            division=make_geo(division),
            district=make_geo(district),
            upazila=make_geo(upazila),
            union=make_geo(union),
            meta=ProfileMeta(
                division_id=user.division_id,
                district_id=user.district_id,
                upazila_id=user.upazila_id,
                union_id=user.union_id,
            ),
        )

    async def get_profile(self, user: User) -> ProfileResponse:
        """Retrieve farmer profile with joined geographic display names."""
        row = await self.repo.get_profile(user.id)
        if not row:
            raise UserNotFoundError("profile")
        return self._format_profile(row)

    async def update_profile(self, user: User, payload) -> ProfileResponse:
        """Dynamically update farmer profile fields, validating geo relations and immutability."""
        values = payload.model_dump(exclude_unset=True)
        if not values:
            raise InvalidProfileDataError(
                "কমপক্ষে একটি পরিবর্তনযোগ্য ফিল্ড প্রদান করুন / At least one modifiable field must be provided."
            )

        # Phone number immutability rule
        if "phone_number" in values or "phoneNumber" in values:
            raise InvalidProfileDataError(
                "ফোন নম্বর পরিবর্তন করা যাবে না / Phone number is immutable and cannot be changed."
            )

        row = await self.repo.get_profile(user.id)
        if not row:
            raise UserNotFoundError("profile")
        current_user = row[0]

        geo_keys = ("division_id", "district_id", "upazila_id", "union_id")
        if any(key in values for key in geo_keys):
            # If a higher geo level changed and children are not explicitly provided in values,
            # reset children rather than keeping mismatched old IDs.
            new_division = values.get("division_id")
            if "division_id" in values and new_division != current_user.division_id:
                if "district_id" not in values:
                    values["district_id"] = None
                if "upazila_id" not in values:
                    values["upazila_id"] = None
                if "union_id" not in values:
                    values["union_id"] = None

            new_district = values.get("district_id")
            if "district_id" in values and new_district != current_user.district_id:
                if "upazila_id" not in values:
                    values["upazila_id"] = None
                if "union_id" not in values:
                    values["union_id"] = None

            new_upazila = values.get("upazila_id")
            if "upazila_id" in values and new_upazila != current_user.upazila_id:
                if "union_id" not in values:
                    values["union_id"] = None

            eff_division = values.get("division_id", current_user.division_id)
            eff_district = values.get("district_id", current_user.district_id)
            eff_upazila = values.get("upazila_id", current_user.upazila_id)
            eff_union = values.get("union_id", current_user.union_id)
            await self._validate_geo_hierarchy(eff_division, eff_district, eff_upazila, eff_union)

        updated_row = await self.repo.update_profile(user.id, values)
        if not updated_row:
            raise UserNotFoundError("profile")

        # Sync profile changes to Supabase cloud database
        try:
            sb_payload = {k: v for k, v in values.items() if k != "updated_at"}
            await supabase_client.update_user_profile(str(user.id), sb_payload)
        except Exception:
            pass

        # Read from the same transaction after UPDATE so the response reflects persisted values.
        persisted_row = await self.repo.get_profile(user.id)
        if not persisted_row:
            raise UserNotFoundError("profile")
        return self._format_profile(persisted_row)

    async def _validate_geo_hierarchy(
        self,
        division_id: uuid.UUID | None,
        district_id: uuid.UUID | None,
        upazila_id: uuid.UUID | None,
        union_id: uuid.UUID | None,
    ) -> None:
        """Validate geographic foreign key relations and BBS hierarchy."""
        if division_id and not await self.repo.check_geo_exists(Division, division_id):
            raise InvalidProfileDataError("বিভাগটি খুঁজে পাওয়া যায়নি / Selected division was not found.")

        if district_id:
            exists = await self.repo.check_geo_exists(
                District, district_id, District.division_id, division_id
            )
            if not exists:
                raise InvalidProfileDataError(
                    "জেলাটি নির্বাচিত বিভাগের আওতাভুক্ত নয় / Selected district does not belong to the chosen division."
                )

        if upazila_id:
            exists = await self.repo.check_geo_exists(
                Upazila, upazila_id, Upazila.district_id, district_id
            )
            if not exists:
                raise InvalidProfileDataError(
                    "উপজেলাটি নির্বাচিত জেলার আওতাভুক্ত নয় / Selected upazila does not belong to the chosen district."
                )

        if union_id:
            exists = await self.repo.check_geo_exists(
                Union, union_id, Union.upazila_id, upazila_id
            )
            if not exists:
                raise InvalidProfileDataError(
                    "ইউনিয়নটি নির্বাচিত উপজেলার আওতাভুক্ত নয় / Selected union does not belong to the chosen upazila."
                )

    async def upload_avatar(self, user: User, upload: UploadFile) -> ProfileResponse:
        """Validate, store avatar locally, and update user avatar_url."""
        content_type = (upload.content_type or "").lower()
        extension = ALLOWED_AVATAR_TYPES.get(content_type)
        if not extension:
            raise InvalidProfileDataError(
                "কেবল JPEG, PNG অথবা WebP ফরম্যাটের ছবি গ্রহণযোগ্য / Only JPEG, PNG, or WebP images are allowed."
            )

        content = await upload.read(MAX_AVATAR_SIZE + 1)
        if len(content) == 0:
            raise InvalidProfileDataError("আপলোড করা ফাইলটি খালি / Uploaded file is empty.")
        if len(content) > MAX_AVATAR_SIZE:
            raise InvalidProfileDataError(
                "ছবির আকার সর্বোচ্চ ২ মেগাবাইট (2MB) হতে পারবে / Maximum image size is 2MB."
            )

        # Minimal collision-free naming using user_id and timestamp
        timestamp = int(datetime.now(timezone.utc).timestamp())
        filename = f"{user.id}_{timestamp}{extension}"
        checksum = hashlib.sha256(content).hexdigest()
        relative_path = f"avatars/{filename}"

        if settings.storage_provider == "supabase" and settings.supabase_url:
            # Upload to Supabase Storage Bucket configured in .env
            public_url = await supabase_client.upload_storage_file(
                bucket=settings.storage_bucket_name,
                path=relative_path,
                content=content,
                mime_type=content_type,
            )
            if not public_url:
                raise InvalidProfileDataError(
                    "ছবি ক্লাউড স্টোরেজে আপলোড করতে সমস্যা হয়েছে / Failed to upload image to Supabase storage."
                )
        else:
            # Fallback to local storage (written off-thread to prevent event loop blocking)
            def _write_local():
                avatars_dir = Path(settings.upload_dir) / "avatars"
                avatars_dir.mkdir(parents=True, exist_ok=True)
                file_path = avatars_dir / filename
                file_path.write_bytes(content)

            import asyncio
            await asyncio.to_thread(_write_local)
            public_url = f"{settings.public_base_url.rstrip('/')}/static/avatars/{filename}"

        # 1. Update avatar_url in local auth.users
        await self.repo.set_avatar(user.id, public_url)

        # 2. Track in system.files table
        await self.repo.record_avatar_file(
            user_id=user.id,
            original_name=upload.filename or filename,
            storage_path=f"/{relative_path}",
            public_url=public_url,
            mime_type=content_type,
            file_size_bytes=len(content),
            checksum=checksum,
            bucket_name=settings.storage_bucket_name,
            provider=settings.storage_provider,
        )

        try:
            await supabase_client.update_user_profile(str(user.id), {"avatar_url": public_url})
        except Exception:
            pass
        return await self.get_profile(user)

    async def delete_avatar(self, user: User) -> None:
        """Clear user avatar_url and delete from Supabase storage if applicable."""
        old_profile_row = await self.repo.get_profile(user.id)
        if old_profile_row and old_profile_row[0].avatar_url:
            old_url = old_profile_row[0].avatar_url
            if f"/object/public/{settings.storage_bucket_name}/" in old_url:
                path = old_url.split(f"/object/public/{settings.storage_bucket_name}/")[-1]
                await supabase_client.delete_storage_file(settings.storage_bucket_name, path)

        await self.repo.set_avatar(user.id, None)
        await self.repo.soft_delete_avatar_files(user.id)
        try:
            await supabase_client.update_user_profile(str(user.id), {"avatar_url": None})
        except Exception:
            pass
