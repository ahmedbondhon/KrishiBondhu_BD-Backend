"""
core/responses.py
=================
Standardized API response builders for the KrishiBondhu platform.

All API responses follow the unified envelope format defined in the
Implementation Plan (Section 5), ensuring frontend clients always
receive a consistent JSON structure.

Success format:
    {
        "success": true,
        "message": "...",
        "data": { ... },
        "meta": { "timestamp": "2026-10-20T23:20:00Z" }
    }

Error format:
    {
        "success": false,
        "message": "...",
        "error": { "code": "...", "details": [...] },
        "meta": { "timestamp": "2026-10-20T23:20:00Z" }
    }
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import json
import uuid

from fastapi.responses import JSONResponse


def _now_utc_iso() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


class _UUIDEncoder(json.JSONEncoder):
    """JSON encoder that handles UUID and datetime objects."""
    def default(self, obj: Any) -> Any:
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def _jsonable(data: Any) -> Any:
    """Recursively convert UUID/datetime values to JSON-safe types."""
    return json.loads(json.dumps(data, cls=_UUIDEncoder))


def success_response(
    data: Any,
    message: str = "Success",
    status_code: int = 200,
    meta: Optional[Dict] = None,
) -> JSONResponse:
    """
    Build a standard success JSON response.

    Args:
        data        : The response payload (dict, list, or any serializable type).
        message     : Human-readable success message.
        status_code : HTTP status code (default 200).
        meta        : Optional extra metadata merged with the timestamp.
    """
    response_meta = {"timestamp": _now_utc_iso()}
    if meta:
        response_meta.update(meta)

    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": _jsonable(data),
            "meta": response_meta,
        },
    )


def error_response(
    message: str,
    error_code: str,
    status_code: int = 400,
    details: Optional[Any] = None,
    raw_detail: Optional[Any] = None,
) -> JSONResponse:
    """
    Build a standard error JSON response.

    Args:
        message     : High-level error description (English).
        error_code  : Machine-readable error code (e.g., 'VALIDATION_ERROR').
        status_code : HTTP status code (default 400).
        details     : Optional list of field-level validation errors.
        raw_detail  : Optional raw detail payload (for dict detail compatibility).
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "detail": raw_detail if raw_detail is not None else message,
            "error": {
                "code": error_code,
                "details": details or [],
            },
            "meta": {"timestamp": _now_utc_iso()},
        },
    )


