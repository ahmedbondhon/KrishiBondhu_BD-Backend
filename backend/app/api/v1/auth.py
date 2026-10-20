# ============================================================================
# KrishiBondhu Bangladesh — Auth API Routes (v1)
# Multi-step registration, OTP verification, passwordless login,
# password reset, language toggle, and helpline support endpoints
# ============================================================================

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, require_roles
from app.core.security import limiter
from app.db.session import get_db
from app.repositories.auth import AuthRepository
from app.schemas.auth import (
    AdminCreateUserRequest,
    DistrictResponse,
    DivisionResponse,
    ExpertRegisterRequest,
    FarmerAgentRegisterRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    MeResponse,
    MessageResponse,
    OtpLoginRequest,
    OtpLoginVerifyRequest,
    RefreshTokenRequest,
    RegisterResponse,
    ResetPasswordRequest,
    SendOtpRequest,
    SendOtpResponse,
    SupportContactResponse,
    TokenResponse,
    UnionResponse,
    UpazilaResponse,
    UpdateLanguageRequest,
    UserResponse,
    VerifyOtpRequest,
    VerifyOtpResponse,
)
from app.services.auth import AuthService, _user_to_response

router = APIRouter(prefix="/auth", tags=["Authentication"])
geo_router = APIRouter(prefix="/geo", tags=["Geographic Hierarchy"])


# ==========================================================================
# Dependencies & Helpers
# ==========================================================================

def get_auth_service(db: Annotated[AsyncSession, Depends(get_db)]) -> AuthService:
    return AuthService(db)


def get_auth_repo(db: Annotated[AsyncSession, Depends(get_db)]) -> AuthRepository:
    return AuthRepository(db)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
AuthRepoDep = Annotated[AuthRepository, Depends(get_auth_repo)]


def _client_info(request: Request) -> tuple[str | None, str | None]:
    return (request.client.host if request.client else None), request.headers.get("user-agent")


# ==========================================================================
# 1. Multi-Step Registration: Step 1 (OTP Verification)
# ==========================================================================

@router.post("/otp/send", response_model=SendOtpResponse, response_model_exclude_none=True, summary="ধাপ ১: ওটিপি কোড পাঠান (Send OTP)")
@router.post("/request-otp", response_model=SendOtpResponse, response_model_exclude_none=True, include_in_schema=False)
@limiter.limit("10/10minute")
async def send_otp(payload: SendOtpRequest, request: Request, service: AuthServiceDep):
    ip_address, _ = _client_info(request)
    result = await service.otp_service.send_otp(
        phone_number=payload.phone_number, purpose=payload.purpose, ip_address=ip_address
    )
    return SendOtpResponse(**result)


@router.post("/otp/verify", response_model=VerifyOtpResponse, summary="ধাপ ১: ওটিপি কোড যাচাই (Verify OTP)")
@router.post("/verify-otp", response_model=VerifyOtpResponse, include_in_schema=False)
async def verify_otp(payload: VerifyOtpRequest, service: AuthServiceDep):
    result = await service.otp_service.verify_otp(
        phone_number=payload.phone_number, otp_code=payload.otp_code, purpose=payload.purpose
    )
    return VerifyOtpResponse(**result)


# ==========================================================================
# 2. Multi-Step Registration: Step 2 & Step 3 (Profile & Consents)
# ==========================================================================

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED, summary="কৃষক / এজেন্ট পূর্ণাঙ্গ রেজিস্ট্রেশন")
async def register_farmer_agent(payload: FarmerAgentRegisterRequest, request: Request, service: AuthServiceDep):
    ip, ua = _client_info(request)
    user, tokens = await service.register_farmer_agent(payload, ip_address=ip, user_agent=ua)
    return RegisterResponse(
        message="রেজিস্ট্রেশন সফল হয়েছে। কৃষিবন্ধু প্ল্যাটফর্মে আপনাকে স্বাগতম!",
        user=_user_to_response(user),
        tokens=tokens,
    )


@router.post("/register/expert", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED, summary="কৃষি বিশেষজ্ঞ / কর্মকর্তা রেজিস্ট্রেশন")
async def register_expert(payload: ExpertRegisterRequest, request: Request, service: AuthServiceDep):
    ip, ua = _client_info(request)
    user, _ = await service.register_expert(payload, ip_address=ip, user_agent=ua)
    return RegisterResponse(
        message="বিশেষজ্ঞ রেজিস্ট্রেশন জমা হয়েছে। অ্যাডমিন অনুমোদনের পর অ্যাকাউন্ট সক্রিয় হবে।",
        user=_user_to_response(user),
    )


@router.post("/register/admin", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED, summary="অ্যাডমিন অ্যাকাউন্ট তৈরি (Admin Only)")
async def create_admin(payload: AdminCreateUserRequest, current_user: CurrentUser, service: AuthServiceDep):
    user, role_code = await service.create_admin_user(payload, created_by=current_user)
    return RegisterResponse(
        message=f"Admin user created successfully with role '{role_code}'.",
        user=_user_to_response(user),
    )


# ==========================================================================
# 2.1 Admin User Management: Approve & Reject Accounts
# ==========================================================================

@router.patch("/admin/users/{user_id}/approve", summary="বিশেষজ্ঞ অ্যাকাউন্ট অনুমোদন", dependencies=[Depends(require_roles("administrator"))])
async def approve_user(user_id: uuid.UUID, current_user: CurrentUser, request: Request, service: AuthServiceDep):
    ip, _ = _client_info(request)
    user = await service.approve_user(user_id=user_id, admin_user=current_user, ip_address=ip)
    return {
        "message": f"User '{user.full_name}' ({user.phone_number}) has been approved.",
        "user_id": str(user.id),
        "status": user.status,
        "is_active": user.is_active,
    }


@router.patch("/admin/users/{user_id}/reject", summary="অ্যাকাউন্ট প্রত্যাখ্যান", dependencies=[Depends(require_roles("administrator"))])
async def reject_user(
    user_id: uuid.UUID,
    current_user: CurrentUser,
    request: Request,
    service: AuthServiceDep,
    reason: str | None = Query(default=None, description="Reason for rejection"),
):
    ip, _ = _client_info(request)
    user = await service.reject_user(user_id=user_id, admin_user=current_user, reason=reason, ip_address=ip)
    return {
        "message": f"User '{user.full_name}' ({user.phone_number}) has been rejected.",
        "user_id": str(user.id),
        "status": user.status,
        "is_active": user.is_active,
    }


# ==========================================================================
# 3. লগইন (Login Options)
# ==========================================================================

@router.post("/login", response_model=TokenResponse, summary="ক) সাধারণ লগইন (Password / PIN Login)")
@limiter.limit("10/minute")
async def login(payload: LoginRequest, request: Request, service: AuthServiceDep):
    ip, ua = _client_info(request)
    return await service.login(payload, ip_address=ip, user_agent=ua)


@router.post("/login/otp-request", response_model=SendOtpResponse, summary="খ) ওটিপি লগইন: ওটিপি পাঠান")
async def request_otp_login(payload: OtpLoginRequest, service: AuthServiceDep):
    return SendOtpResponse(**(await service.request_otp_login(phone_number=payload.phone_number)))


@router.post("/login/otp-verify", response_model=TokenResponse, summary="খ) ওটিপি লগইন: ওটিপি যাচাই ও তাৎক্ষণিক লগইন")
@limiter.limit("10/minute")
async def verify_otp_login(payload: OtpLoginVerifyRequest, request: Request, service: AuthServiceDep):
    ip, ua = _client_info(request)
    return await service.verify_otp_login(
        phone_number=payload.phone_number,
        otp_code=payload.otp_code,
        remember_me=payload.remember_me,
        ip_address=ip,
        user_agent=ua,
    )


# ==========================================================================
# 4. পাসওয়ার্ড ভুলে গেছেন? (Forgot Password / Reset with OTP)
# ==========================================================================

@router.post("/password/forgot", response_model=SendOtpResponse, summary="পাসওয়ার্ড ভুলে গেছেন: ওটিপি পাঠান")
@router.post("/forgot-password", response_model=SendOtpResponse, response_model_exclude_none=True, include_in_schema=False)
async def forgot_password(payload: ForgotPasswordRequest, service: AuthServiceDep):
    return SendOtpResponse(**(await service.forgot_password_request(phone_number=payload.phone_number)))


@router.post("/password/reset", response_model=MessageResponse, summary="পাসওয়ার্ড রিসেট করুন")
@router.post("/reset-password", response_model=MessageResponse, include_in_schema=False)
async def reset_password(payload: ResetPasswordRequest, service: AuthServiceDep):
    await service.reset_password(payload)
    return MessageResponse(message="পাসওয়ার্ড সফলভাবে পরিবর্তন করা হয়েছে। নতুন পাসওয়ার্ড দিয়ে লগইন করুন।")


# ==========================================================================
# 5. ভাষা পরিবর্তন ও হেল্পলাইন (Language Toggle & Support)
# ==========================================================================

@router.patch("/profile/language", response_model=UserResponse, summary="পছন্দের ভাষা পরিবর্তন (bn / en)")
async def update_language(payload: UpdateLanguageRequest, current_user: CurrentUser, service: AuthServiceDep):
    updated_user = await service.update_language(current_user.id, payload.preferred_language)
    return _user_to_response(updated_user)


@router.get("/support", response_model=SupportContactResponse, summary="সহায়তা / হেল্পলাইন তথ্য")
async def get_support_info(service: AuthServiceDep):
    return await service.get_support_contact()


# ==========================================================================
# 6. টোকেন, সেশন ও ইমেইল যাচাইকরণ (Session & Email Verification)
# ==========================================================================

@router.post("/refresh", response_model=TokenResponse, summary="টোকেন রিফ্রেশ (Refresh Token)")
async def refresh_token(payload: RefreshTokenRequest, service: AuthServiceDep):
    return await service.refresh_tokens(payload.refresh_token)


@router.post("/logout", response_model=MessageResponse, summary="লগআউট (Logout)")
async def logout(payload: LogoutRequest, service: AuthServiceDep):
    await service.logout(payload.refresh_token)
    return MessageResponse(message="Logged out successfully.")


@router.post("/logout/all", response_model=MessageResponse, summary="সকল ডিভাইস থেকে লগআউট")
async def logout_all(current_user: CurrentUser, service: AuthServiceDep):
    await service.logout_all(current_user.id)
    return MessageResponse(message="Logged out from all devices.")


@router.get("/me", response_model=MeResponse, summary="বর্তমান ব্যবহারকারীর প্রোফাইল")
async def get_me(current_user: CurrentUser):
    return _user_to_response(current_user)


@router.get("/verify-email", summary="ইমেইল যাচাইকরণ (GET)")
@router.post("/verify-email", summary="ইমেইল যাচাইকরণ (POST)")
async def verify_email(service: AuthServiceDep, token: str = Query(..., description="Email verification token")):
    user = await service.verify_email_token(token)
    return {
        "message": f"Email '{user.email}' has been successfully verified.",
        "user_id": str(user.id),
        "email": user.email,
        "email_verified": user.email_verified,
    }


@router.post("/verify-email/request", summary="ইমেইল যাচাই লিংক পাঠান")
async def request_verification_email(current_user: CurrentUser, service: AuthServiceDep):
    if not current_user.email:
        raise HTTPException(status_code=400, detail="User account does not have an email address.")
    if current_user.email_verified:
        return {"message": "Email is already verified.", "email_verified": True}

    service.generate_email_verification_token(current_user.id, current_user.email)
    return {
        "message": f"Verification email dispatched to {current_user.email}.",
        "email": current_user.email,
        "expires_in_hours": 24,
    }


# ==========================================================================
# 7. Geographic Hierarchy Endpoints
# ==========================================================================

@geo_router.get("/divisions", response_model=list[DivisionResponse], summary="বিভাগ তালিকা")
async def get_divisions(repo: AuthRepoDep):
    return await repo.get_divisions()


@geo_router.get("/districts", response_model=list[DistrictResponse], summary="জেলা তালিকা")
async def get_districts(repo: AuthRepoDep, division_id: uuid.UUID | None = Query(default=None)):
    return await repo.get_districts(division_id=division_id)


@geo_router.get("/upazilas", response_model=list[UpazilaResponse], summary="উপজেলা তালিকা")
async def get_upazilas(repo: AuthRepoDep, district_id: uuid.UUID | None = Query(default=None)):
    return await repo.get_upazilas(district_id=district_id)


@geo_router.get("/unions", response_model=list[UnionResponse], summary="ইউনিয়ন তালিকা")
async def get_unions(repo: AuthRepoDep, upazila_id: uuid.UUID | None = Query(default=None)):
    return await repo.get_unions(upazila_id=upazila_id)