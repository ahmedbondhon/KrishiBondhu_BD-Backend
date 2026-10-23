"""
main.py
=======
KrishiBondhu Bangladesh — FastAPI Application Entry Point

This file:
  1. Creates the FastAPI application instance.
  2. Registers global middleware (CORS, request logging).
  3. Registers all API routers.
  4. Adds startup/shutdown event handlers for DB connection validation.
  5. Registers a global exception handler for clean Bangla error responses.

To run the development server:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Or using the start script:
    python -m uvicorn app.main:app --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_v1_router
from app.core.config import settings
from app.db.session import engine

# ── Logging ───────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("krishibondhu")


# ── Lifespan (Startup & Shutdown) ─────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown events.

    On startup:
      - Validates database connectivity.
      - Logs the application mode.

    On shutdown:
      - Disposes the database connection pool.
    """
    logger.info(f"🌾 KrishiBondhu API starting up [{settings.environment}]")
    logger.info(f"📡 Database: {settings.database_url.split('@')[-1]}")
    logger.info(f"🤖 AI Confidence Threshold: {settings.ai_confidence_threshold}")

    try:
        async with engine.begin() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection verified.")
    except Exception as e:
        logger.error(f"❌ Database connection FAILED: {e}")

    try:
        import asyncio
        from app.services.storage_service import storage_service
        await asyncio.to_thread(storage_service.warmup)
        logger.info("✅ Storage service initialized.")
    except Exception as e:
        logger.warning(f"⚠️ Storage service warmup skipped: {e}")

    yield  # Application is running

    logger.info("🛑 KrishiBondhu API shutting down...")
    await engine.dispose()
    logger.info("✅ Database connections closed.")


# ── FastAPI Application ───────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
## KrishiBondhu Bangladesh — ChashiGuard API

AI-powered crop disease diagnosis platform for Bangladeshi farmers.

### Key Features:
- **Authentication**: JWT-based with RBAC (farmer, agent, expert, admin)
- **ChashiGuard**: AI crop disease diagnosis with Bangla advisory
- **Expert Review**: Human-in-the-loop expert validation for low-confidence cases
- **Signed Uploads**: Two-step secure image upload to Supabase/S3

### Bangla Language:
All farmer-facing messages and advisory content are in Bangla (বাংলা).

### API Prefix:
- Public API: `/api/v1/`
- Internal AI service calls: `/internal/v1/`
    """,
    openapi_url="/api/v1/openapi.json" if not settings.environment == "production" else None,
    docs_url="/api/v1/docs" if not settings.environment == "production" else None,
    redoc_url="/api/v1/redoc" if not settings.environment == "production" else None,
    lifespan=lifespan,
)

# ── CORS Middleware ───────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static / Uploads Mount ───────────────────────────────
from pathlib import Path
from fastapi.staticfiles import StaticFiles

Path(settings.upload_dir, "avatars").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=settings.upload_dir), name="static")
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")




# ── Global Exception Handlers ─────────────────────────────

from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.responses import error_response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Format standard HTTPException / StarletteHTTPException into the unified
    KrishiBondhu error envelope format.
    """
    code = f"HTTP_{exc.status_code}"
    message = "Request failed"
    details = []

    if isinstance(exc.detail, dict):
        code = exc.detail.get("code", code)
        message = exc.detail.get("message", exc.detail.get("message_bn", "Error"))
        if "message_bn" in exc.detail:
            details.append({"message_bn": exc.detail["message_bn"]})
        if "details" in exc.detail and isinstance(exc.detail["details"], list):
            details.extend(exc.detail["details"])
    elif isinstance(exc.detail, str):
        message = exc.detail
    elif isinstance(exc.detail, list):
        details = exc.detail

    return error_response(
        message=message,
        error_code=code,
        status_code=exc.status_code,
        details=details if details else None,
        raw_detail=exc.detail,
    )



from sqlalchemy.exc import IntegrityError


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """
    Handle database constraint violations (ForeignKeyViolation, UniqueViolation, etc.)
    and return clean, human-friendly Bangla messages instead of 500 crashes.
    """
    error_str = str(exc.orig if hasattr(exc, "orig") else exc).lower()
    if "foreign key" in error_str or "violates foreign key constraint" in error_str:
        return error_response(
            message="Foreign key reference constraint violated",
            error_code="FOREIGN_KEY_VIOLATION",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=[{"message_bn": "প্রদত্ত আইডি বা রেফারেন্স ডাটাবেজে খুঁজে পাওয়া যায়নি। অনুগ্রহ করে সঠিক তথ্য প্রদান করুন।"}],
        )
    elif "unique" in error_str or "violates unique constraint" in error_str:
        return error_response(
            message="Unique constraint violated",
            error_code="UNIQUE_VIOLATION",
            status_code=status.HTTP_409_CONFLICT,
            details=[{"message_bn": "এই তথ্যটি ইতিমধ্যে ডাটাবেজে বিদ্যমান আছে।"}],
        )
    else:
        return error_response(
            message="Database integrity error",
            error_code="INTEGRITY_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=[{"message_bn": "ডাটাবেজ নিয়মের অসংগতির কারণে অনুরোধটি সম্পন্ন করা সম্ভব হয়নি।"}],
        )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Convert FastAPI/Pydantic validation errors into the standard KrishiBondhu
    error envelope format with Bangla field-level messages.
    """
    from datetime import datetime, timezone

    details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        details.append({"field": field, "message": error["msg"]})

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Validation failed",
            "error": {
                "code": "VALIDATION_ERROR",
                "details": details,
            },
            "meta": {"timestamp": datetime.now(timezone.utc).isoformat()},
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all for unexpected server errors — prevents stack traces leaking to clients."""
    from datetime import datetime, timezone
    logger.exception(f"Unhandled exception on {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Internal server error",
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "details": [],
            },
            "meta": {"timestamp": datetime.now(timezone.utc).isoformat()},
        },
    )


# ── Routers ───────────────────────────────────────────────
app.include_router(api_v1_router)


# ── Health Check ──────────────────────────────────────────
@app.get("/health", tags=["Health"], summary="API health check")
async def health_check():
    """Simple health check endpoint — used by load balancers and monitoring."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


# ── Root ──────────────────────────────────────────────────
@app.get("/", tags=["Root"], include_in_schema=False)
async def root():
    return {
        "message": "KrishiBondhu Bangladesh API is running. See /api/v1/docs for documentation.",
        "docs": "/api/v1/docs",
    }
