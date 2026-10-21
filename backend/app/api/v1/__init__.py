"""
api/v1/__init__.py
==================
v1 API router registration.
All sub-routers for the /api/v1 prefix are assembled here.
Import this in main.py and include it with app.include_router().
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.farms import router as farms_router
from app.api.v1.files import router as files_router
from app.api.v1.diagnosis import router as diagnosis_router, expert_router
from app.api.v1.notifications import router as notifications_router

# Master v1 router — all routes grouped under /api/v1
api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth_router)           # /api/v1/auth/...
api_v1_router.include_router(farms_router)          # /api/v1/farms/...
api_v1_router.include_router(files_router)          # /api/v1/files/...
api_v1_router.include_router(diagnosis_router)      # /api/v1/diagnosis-cases/...
api_v1_router.include_router(expert_router)         # /api/v1/expert/...
api_v1_router.include_router(notifications_router)  # /api/v1/notifications/...
