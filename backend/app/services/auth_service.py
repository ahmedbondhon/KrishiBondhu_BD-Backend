"""
services/auth_service.py
========================
Business logic for user registration, authentication, and profile management.

Why a service layer?
  Routes (api/v1/auth.py) should only handle HTTP concerns (parsing requests,
  returning responses). Business logic lives here — separated so it can be
  tested independently of HTTP.

Key methods:
  - register_user()  : Validate uniqueness, hash password, create user record.
  - authenticate()   : Verify credentials, issue JWT tokens.
  - refresh_tokens() : Validate refresh token, issue new token pair.
  - get_user_by_id() : Load a user with their role relationship.
  - update_profile() : Update farmer location/communication preferences.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_refresh_token,
)
from app.models.auth import Role, User
from app.schemas.auth import RegisterRequest, UpdateProfileRequest


class AuthService:
    """Handles all authentication and user profile operations."""

    async def register_user(self, db: AsyncSession, payload: RegisterRequest) -> User:
        """
        Register a new user account.

        Steps:
          1. Check phone number is not already taken.
          2. Resolve the role_code to a Role FK.
          3. Hash the password with Argon2.
          4. Insert the new User record.
        """
        # 1. Check for duplicate phone number
        existing = await db.execute(
            select(User).where(User.phone_number == payload.phone_number)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "PHONE_ALREADY_REGISTERED",
                    "message_bn": "এই ফোন নম্বরটি ইতিমধ্যে নিবন্ধিত আছে।",
                },
            )

        # 2. Resolve role (enforce farmer role for public registration)
        if payload.role_code != "farmer":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "ROLE_NOT_PERMITTED", "message_bn": "শুধুমাত্র কৃষক হিসেবে সরাসরি নিবন্ধন করা যাবে।"},
            )

        role_result = await db.execute(
            select(Role).where(Role.code == payload.role_code)
        )
        role = role_result.scalar_one_or_none()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_ROLE", "message_bn": "অবৈধ ভূমিকা।"},
            )

        # 3. Create user
        user = User(
            phone_number=payload.phone_number,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
            role_id=role.id,
        )
        db.add(user)
        await db.flush()  # Get user.id without committing

        # Eagerly load role for response
        await db.refresh(user, ["role"])
        return user

    async def authenticate(
        self, db: AsyncSession, phone_number: str, password: str
    ) -> tuple[str, str]:
        """
        Authenticate credentials and return (access_token, refresh_token).

        Raises 401 if phone number not found or password doesn't match.
        Uses constant-time comparison to prevent timing attacks.
        """
        result = await db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(User.phone_number == phone_number, User.is_deleted == False)
        )
        user = result.scalar_one_or_none()

        if not user or not user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_CREDENTIALS", "message_bn": "ফোন নম্বর বা পাসওয়ার্ড ভুল।"},
            )

        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_CREDENTIALS", "message_bn": "ফোন নম্বর বা পাসওয়ার্ড ভুল।"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "ACCOUNT_DISABLED", "message_bn": "আপনার অ্যাকাউন্ট নিষ্ক্রিয় করা হয়েছে।"},
            )

        access_token = create_access_token(user.id, user.role.code)
        refresh_token = create_refresh_token(user.id)
        return access_token, refresh_token

    async def refresh_tokens(
        self, db: AsyncSession, refresh_token: str
    ) -> tuple[str, str]:
        """
        Validate a refresh token and issue a new token pair.
        Refresh token rotation: every refresh issues a brand-new pair.
        """
        user_id_str = verify_refresh_token(refresh_token)
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_REFRESH_TOKEN", "message_bn": "সেশন মেয়াদ শেষ। পুনরায় লগইন করুন।"},
            )

        result = await db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(User.id == UUID(user_id_str), User.is_active == True, User.is_deleted == False)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "USER_NOT_FOUND", "message_bn": "ব্যবহারকারী পাওয়া যায়নি।"},
            )

        access_token = create_access_token(user.id, user.role.code)
        new_refresh_token = create_refresh_token(user.id)
        return access_token, new_refresh_token

    async def get_user_with_role(self, db: AsyncSession, user_id: UUID) -> User:
        """Load a user with their role relationship eagerly loaded."""
        result = await db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_profile(
        self, db: AsyncSession, user: User, payload: UpdateProfileRequest
    ) -> User:
        """Update mutable profile fields (geo location, language preference, name, avatar)."""
        update_data = payload.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        await db.flush()
        return user
