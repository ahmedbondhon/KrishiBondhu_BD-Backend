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


# ── Global Exception Handlers ─────────────────────────────

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
