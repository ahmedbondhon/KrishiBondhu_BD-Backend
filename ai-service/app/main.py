"""
ai-service/app/main.py
======================
KrishiBondhu Bangladesh — Internal AI Microservice

This is a SEPARATE FastAPI application from the main backend.
It is only accessible internally (not exposed publicly) and serves:

  POST /internal/v1/image-quality/check       → Validate image quality before diagnosis
  POST /internal/v1/crop-diagnosis/predict    → Run AI crop disease prediction

Architecture:
  - In production: the main backend calls this service via HTTP (httpx AsyncClient).
  - In development: mock responses are returned when this service is unavailable.
  - The AI model is loaded once at startup and cached in memory.

To run this service:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

Internal URL (referenced in backend .env):
    AI_SERVICE_URL=http://localhost:8001
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

# ── Logging ───────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("krishibondhu.ai-service")


# ── Lifespan ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load AI model artifacts at startup."""
    logger.info("🤖 KrishiBondhu AI Service starting up...")
    logger.info("📦 Loading model registry...")

    # In production this would load a TensorFlow/PyTorch/ONNX model.
    # For the MVP stub we skip actual model loading.
    app.state.model_loaded = True
    app.state.model_version = "v1.0.0"
    app.state.model_name = "krishibondhu-crop-vision"

    logger.info(f"✅ Model '{app.state.model_name}' ({app.state.model_version}) ready.")

    yield  # Service is running

    logger.info("🛑 AI Service shutting down...")


# ── FastAPI Application ───────────────────────────────────
app = FastAPI(
    title="KrishiBondhu AI Service",
    version="1.0.0",
    description="""
## KrishiBondhu AI Microservice

Internal service for crop disease detection. NOT publicly exposed.

### Endpoints:
- `POST /internal/v1/image-quality/check` — Validate image quality
- `POST /internal/v1/crop-diagnosis/predict` — AI crop disease prediction
    """,
    docs_url="/internal/docs",
    redoc_url="/internal/redoc",
    openapi_url="/internal/openapi.json",
    lifespan=lifespan,
)


# ── Register Internal Routers ─────────────────────────────
from app.api.internal import router as internal_router  # noqa: E402
app.include_router(internal_router)


# ── Health Check ──────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "healthy",
        "service": "KrishiBondhu AI Service",
        "model_loaded": getattr(app.state, "model_loaded", False),
        "model_version": getattr(app.state, "model_version", "unknown"),
    }


# ── Global Exception Handler ──────────────────────────────
@app.exception_handler(Exception)
async def catch_all(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal AI service error", "detail": str(exc)},
    )
