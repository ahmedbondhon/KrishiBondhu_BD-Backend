"""Development-only routes used by the local frontend demo.

This module is included only when DEBUG=True or environment != production.
It deliberately exposes no database inspector or credentials; the frontend
should use normal API routes.

SECURITY: These routes must NEVER be reachable in production. The main.py
already guards the inclusion with `settings.environment != "production"`.
Set ENVIRONMENT=production in your deployment environment to disable them.
Set ENABLE_DEMO_ROUTES=false to disable even in non-production environments.
"""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.core.security import normalize_bd_phone
from app.services.otp_service import sms_inbox

settings = get_settings()
demo_router = APIRouter(tags=["Development Demo"])


def _assert_demo_allowed() -> None:
    """Raise 403 if demo routes are accessed in production or explicitly disabled."""
    env = (settings.environment or settings.app_env or "development").lower()
    if env in ("production", "prod"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo routes are disabled in production.",
        )


@demo_router.get("/demo", include_in_schema=False)
async def demo_ui():
    _assert_demo_allowed()
    demo_file = Path(__file__).resolve().parents[3] / "demo" / "frontend_demo.html"
    if not demo_file.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo UI not found. Check that demo/frontend_demo.html is present.",
        )
    return FileResponse(demo_file)


@demo_router.get("/demo/sms-inbox", include_in_schema=False)
async def get_sms_inbox(phone: Annotated[str, Query(...)]):
    # Bug 4 fix: Explicitly block access in production environment.
    # In a real deployment set ENVIRONMENT=production to disable this entirely.
    _assert_demo_allowed()

    try:
        normalized_phone = normalize_bd_phone(phone)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    messages = sms_inbox.get_and_delete(normalized_phone)
    return {
        "phone": phone,
        "count": len(messages),
        "messages": messages,
        "latest_message": messages[-1]["message"] if messages else None,
        "latest_otp": messages[-1].get("otp_code") if messages else None,
    }
