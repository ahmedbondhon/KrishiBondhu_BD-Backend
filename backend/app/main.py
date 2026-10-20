from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from app.api.v1 import api_v1_router
from app.core.config import get_settings
from app.core.security import limiter, rate_limit_exceeded_handler

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Prevent demo/simulator modes in production
    if settings.app_env.lower() == "production" and settings.otp_demo_mode:
        raise RuntimeError("OTP_DEMO_MODE cannot be enabled in production!")
    if not settings.debug and settings.sms_mode == "simulator":
        raise RuntimeError("SMS_MODE=simulator cannot be used when DEBUG=False!")
    yield
    from app.db.session import engine
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    description="কৃষিবন্ধু বাংলাদেশ — Crop diagnosis and advisory platform for smallholder farmers.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

_origins = [o.strip() for o in settings.cors_allowed_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins if _origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "User-Agent", "*"],
)

app.include_router(api_v1_router, prefix=settings.api_v1_prefix)

# Demo UI routes — only in DEBUG mode
if settings.debug:
    from demo.demo import demo_router
    app.include_router(demo_router)


@app.get("/", include_in_schema=False)
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/demo" if settings.debug else "/docs")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    from fastapi.responses import Response
    return Response(content=b"", media_type="image/x-icon")


@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": "1.0.0",
        "debug": settings.debug,
        "sms_mode": settings.sms_mode,
    }
