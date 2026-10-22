from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded

from app.api.v1 import api_v1_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.security import limiter, rate_limit_exceeded_handler

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.app_env.lower() == "production" and settings.otp_demo_mode:
        raise RuntimeError("OTP_DEMO_MODE cannot be enabled in production!")
    if not settings.debug and settings.sms_mode == "simulator":
        raise RuntimeError("SMS_MODE=simulator cannot be used when DEBUG=False!")
    yield
    from app.db.session import engine
    await engine.dispose()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Exception handlers & Rate Limiter
register_exception_handlers(app)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Static & Uploads Mount
Path(settings.upload_dir, "avatars").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=settings.upload_dir), name="static")
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# CORS Middleware
origins = [o.strip() for o in settings.cors_allowed_origins.split(",") if o.strip()]
allow_all = "*" in origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all else origins,
    allow_credentials=not allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(api_v1_router, prefix=settings.api_v1_prefix)
if settings.debug:
    from app.api.demo import demo_router
    app.include_router(demo_router)

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy", "service": settings.app_name, "version": "1.0.0"}