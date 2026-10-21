"""
api/v1/auth.py
==============
HTTP route handlers for authentication endpoints.

Routes:
  POST /api/v1/auth/register  → Register a new user
  POST /api/v1/auth/login     → Login and receive JWT tokens
  POST /api/v1/auth/refresh   → Refresh access token using refresh token
  GET  /api/v1/auth/me        → Get current authenticated user's profile

Each handler:
  1. Parses and validates the request using Pydantic schemas.
  2. Delegates business logic to AuthService.
  3. Returns a standardized response using success_response().

The route handlers do NOT contain business logic — they only bridge
HTTP ↔ service layer.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user, get_db
from app.core.responses import success_response
from app.models.auth import User
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()


@router.post("/register", status_code=201, summary="Register a new user account")
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new farmer, agent, or expert account.

    - Phone number must be a valid Bangladesh mobile number (+880XXXXXXXXXX).
    - Password is hashed with Argon2 (stored hash, never plain text).
    - Default role is 'farmer' if not specified.
    """
    user = await auth_service.register_user(db, payload)
    return success_response(
        data=UserResponse.model_validate(user).model_dump(),
        message="নিবন্ধন সফল হয়েছে।",
        status_code=201,
    )


@router.post("/login", summary="Login and receive JWT tokens")
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate with phone number and password.

    Returns an access token (short-lived) and refresh token (long-lived).
    Store the refresh token securely on the client (HttpOnly cookie recommended).
    """
    access_token, refresh_token = await auth_service.authenticate(
        db, payload.phone_number, payload.password
    )
    return success_response(
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in_minutes=settings.jwt_access_token_expire_minutes,
        ).model_dump(),
        message="লগইন সফল হয়েছে।",
    )


@router.post("/refresh", summary="Get a new access token using a refresh token")
async def refresh_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Exchange a valid refresh token for a new access + refresh token pair.

    Token Rotation: Each call to this endpoint invalidates the old refresh
    token and issues a brand new one. Clients must update stored refresh tokens.
    """
    access_token, new_refresh = await auth_service.refresh_tokens(db, payload.refresh_token)
    return success_response(
        data=TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh,
            token_type="Bearer",
            expires_in_minutes=settings.jwt_access_token_expire_minutes,
        ).model_dump(),
        message="টোকেন রিফ্রেশ সফল।",
    )


@router.get("/me", summary="Get the currently authenticated user's profile")
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns full profile of the currently authenticated user.
    Requires a valid Bearer access token in the Authorization header.
    """
    # Reload with role relationship
    user_with_role = await auth_service.get_user_with_role(db, current_user.id)
    return success_response(
        data=UserResponse.model_validate(user_with_role).model_dump(),
        message="প্রোফাইল তথ্য সফলভাবে পাওয়া গেছে।",
    )


@router.post("/me/profile", summary="Update farmer profile (location, language)")
async def update_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update location and communication preferences for a farmer.
    Supports partial updates — only provided fields are modified.
    """
    updated_user = await auth_service.update_profile(db, current_user, payload)
    user_with_role = await auth_service.get_user_with_role(db, updated_user.id)
    return success_response(
        data=UserResponse.model_validate(user_with_role).model_dump(),
        message="প্রোফাইল সফলভাবে আপডেট হয়েছে।",
    )
