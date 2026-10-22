# ============================================================================
# KrishiBondhu Bangladesh — API v1 Router Aggregator
# ============================================================================

from fastapi import APIRouter

from app.api.v1.auth import geo_router, router as auth_router
from app.api.v1.profile import router as profile_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(geo_router)
api_v1_router.include_router(profile_router)
