# ============================================================================
# KrishiBondhu Bangladesh — Profile Repository
# Database layer for auth.users and geo.* joins
# ============================================================================

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import User
from app.models.geo import District, Division, Union, Upazila
from app.models.system import File


class ProfileRepository:
    """Async repository for farmer profile queries, dynamic updates, and avatar files."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_profile(
        self, user_id: uuid.UUID
    ) -> tuple[User, Division | None, District | None, Upazila | None, Union | None] | None:
        """Fetch user with LEFT JOIN to divisions, districts, upazilas, and unions."""
        stmt = (
            select(User, Division, District, Upazila, Union)
            .outerjoin(Division, User.division_id == Division.id)
            .outerjoin(District, User.district_id == District.id)
            .outerjoin(Upazila, User.upazila_id == Upazila.id)
            .outerjoin(Union, User.union_id == Union.id)
            .where(User.id == user_id, User.is_deleted.is_(False))
        )
        result = await self.db.execute(stmt)
        return result.one_or_none()

    async def update_profile(
        self, user_id: uuid.UUID, values: dict[str, Any]
    ) -> tuple[User, Division | None, District | None, Upazila | None, Union | None] | None:
        """Execute a minimal and dynamic UPDATE query updating only modified fields."""
        if values:
            # Absolute security guard: phone_number is immutable via profile edit
            values.pop("phone_number", None)
            values.pop("phoneNumber", None)
            values["updated_at"] = datetime.now(timezone.utc)

            stmt = (
                update(User)
                .where(User.id == user_id, User.is_deleted.is_(False))
                .values(**values)
            )
            result = await self.db.execute(stmt)
            if result.rowcount != 1:
                return None
            await self.db.flush()

        return await self.get_profile(user_id)

    async def set_avatar(self, user_id: uuid.UUID, avatar_url: str | None) -> None:
        """Update or clear the avatar_url in auth.users."""
        stmt = (
            update(User)
            .where(User.id == user_id, User.is_deleted.is_(False))
            .values(avatar_url=avatar_url, updated_at=datetime.now(timezone.utc))
        )
        await self.db.execute(stmt)
        await self.db.flush()

    async def soft_delete_avatar_files(self, user_id: uuid.UUID) -> None:
        """Mark user's avatar records in system.files as deleted (Bug 3.2)."""
        stmt = (
            update(File)
            .where(
                File.entity_type == "user_avatar",
                File.entity_id == user_id,
                File.is_deleted.is_(False),
            )
            .values(
                is_deleted=True,
                deleted_at=datetime.now(timezone.utc),
            )
        )
        await self.db.execute(stmt)
        await self.db.flush()

    async def record_avatar_file(
        self,
        user_id: uuid.UUID,
        original_name: str,
        storage_path: str,
        public_url: str,
        mime_type: str,
        file_size_bytes: int,
        checksum: str | None = None,
        bucket_name: str = "avatars",
        provider: str = "supabase",
    ) -> File:
        """Record uploaded avatar metadata in system.files table."""
        file_record = File(
            uploaded_by=user_id,
            original_name=original_name,
            storage_path=storage_path,
            bucket_name=bucket_name,
            provider=provider,
            mime_type=mime_type,
            file_size_bytes=file_size_bytes,
            checksum=checksum,
            public_url=public_url,
            entity_type="user_avatar",
            entity_id=user_id,
            is_processed=True,
            is_deleted=False,
        )
        self.db.add(file_record)
        await self.db.flush()
        return file_record

    async def check_geo_exists(
        self,
        model,
        identifier: uuid.UUID,
        parent_column=None,
        parent_id: uuid.UUID | None = None,
    ) -> bool:
        """Verify geographic entity existence and active status with parent relationship."""
        conditions = [model.id == identifier, model.is_active.is_(True)]
        if parent_column is not None and parent_id is not None:
            conditions.append(parent_column == parent_id)
        stmt = select(model.id).where(*conditions)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
