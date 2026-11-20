"""
api/v1/quick_diagnosis.py
=========================
One-call crop diagnosis: upload a photo -> get the result in the same response.

  POST /api/v1/quick-diagnosis        (multipart/form-data)
       image      file (jpg / png / webp, max 5 MB)   required
       crop_name  text, optional hint
       notes      text, optional

Stateless on purpose (for now): no DiagnosisCase row, no storage upload, no DB
session held open during the slow model call. The existing /diagnosis-cases/*
routes are untouched.

The diagnosis itself lives in app/services/diagnosis_engine.py -> replace that
file when you build your own model. Nothing in this router needs to change.

Register once in your api router file:
    from app.api.v1 import quick_diagnosis
    api_router.include_router(quick_diagnosis.router)

Needs: python-multipart (UploadFile), Pillow, httpx
"""

import asyncio
import hashlib
import logging
import os
import time
from collections import OrderedDict
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from app.core.dependencies import require_roles
from app.core.responses import success_response
from app.models.auth import User
from app.services.diagnosis_engine import (
    ENGINE_ID,
    EngineError,
    EngineResult,
    InvalidImageError,
    diagnose,
)
from app.services.diagnosis_service import _confidence_label
from app.services.otp_service import ip_rate_limiter

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Crop Diagnosis (ChashiGuard) - Quick"])

# ─────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}

# Below this the result is treated as "not sure": expert review is requested and
# NO treatment text is shown (same safety rule as the /analyze flow).
# Self-reported LLM confidence is not well calibrated, so keep this conservative.
MIN_CONFIDENCE = float(os.getenv("DIAGNOSIS_MIN_CONFIDENCE", "0.60"))

CACHE_TTL_S = 24 * 60 * 60
CACHE_MAX_ITEMS = 500
USER_DAILY_LIMIT = int(os.getenv("QUICK_DIAG_USER_DAILY_LIMIT", "30"))
IP_LIMIT_PER_10_MIN = 30


# ─────────────────────────────────────────────────────────
# Cost guards: result cache + in-flight de-duplication
# ─────────────────────────────────────────────────────────
class _TTLCache:
    """Tiny in-memory LRU+TTL cache. Per worker process; swap for Redis if you run many workers."""

    def __init__(self, max_items: int, ttl_s: int):
        self._data: "OrderedDict[str, tuple[float, EngineResult]]" = OrderedDict()
        self._max = max_items
        self._ttl = ttl_s

    def get(self, key: str) -> Optional[EngineResult]:
        item = self._data.get(key)
        if item is None:
            return None
        expires_at, value = item
        if expires_at < time.monotonic():
            self._data.pop(key, None)
            return None
        self._data.move_to_end(key)
        return value

    def set(self, key: str, value: EngineResult) -> None:
        self._data[key] = (time.monotonic() + self._ttl, value)
        self._data.move_to_end(key)
        while len(self._data) > self._max:
            self._data.popitem(last=False)


_cache = _TTLCache(CACHE_MAX_ITEMS, CACHE_TTL_S)
_inflight: "dict[str, asyncio.Task]" = {}


def _cache_key(raw: bytes, crop_name: Optional[str]) -> str:
    # Same photo (+ same crop hint, + same engine) => same answer, no second paid call.
    # `notes` is deliberately NOT in the key so re-sending with edited notes stays free.
    h = hashlib.sha256()
    h.update(ENGINE_ID.encode())
    h.update(b"\0")
    h.update((crop_name or "").strip().lower().encode())
    h.update(b"\0")
    h.update(raw)
    return h.hexdigest()


async def _diagnose_and_cache(key: str, raw: bytes, crop: Optional[str], notes: Optional[str]) -> EngineResult:
    result = await diagnose(raw, crop_hint=crop, notes=notes)
    _cache.set(key, result)   # only successful results are cached
    return result


def _enforce_limits(user: User, request: Request) -> None:
    """Only called right before a PAID call (cache hits and joined in-flight calls are free)."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    user_ok = ip_rate_limiter.check_and_record(
        f"quickdiag_user_{user.id}", max_count=USER_DAILY_LIMIT, window_minutes=24 * 60
    )
    ip_ok = ip_rate_limiter.check_and_record(
        f"quickdiag_ip_{client_ip}", max_count=IP_LIMIT_PER_10_MIN, window_minutes=10
    )
    if not (user_ok and ip_ok):
        raise HTTPException(
            status_code=429,
            detail={
                "code": "RATE_LIMIT_EXCEEDED",
                "message_bn": "খুব বেশি বিশ্লেষণ প্রচেষ্টা হয়েছে। কিছুক্ষণ পর আবার চেষ্টা করুন।",
            },
        )


# ─────────────────────────────────────────────────────────
# Response shaping (same field names as GET /diagnosis-cases/{id} where possible)
# ─────────────────────────────────────────────────────────
def _build_payload(result: EngineResult, from_cache: bool) -> dict:
    top = result.predictions[0] if result.predictions else None
    confidence = top.confidence if top else None
    requires_expert = top is None or top.confidence < MIN_CONFIDENCE

    advisory = None
    notice_bn = None
    if requires_expert:
        notice_bn = "নিশ্চিতভাবে রোগ শনাক্ত করা যায়নি। কোনো ওষুধ বা সার প্রয়োগের আগে কৃষি বিশেষজ্ঞের পরামর্শ নিন।"
    else:
        advisory = {
            "title_bn": top.name_bn,
            "summary_bn": result.summary_bn,
            "detailed_treatment_bn": result.treatment_bn,
            "preventive_measures_bn": result.prevention_bn,
            "chemical_recommendations_bn": None,
            "organic_recommendations_bn": None,
            "source": ENGINE_ID,
        }

    return {
        "issue_name_bn": top.name_bn if top else None,
        "issue_name_en": top.name_en if top else None,
        "crop": result.crop,
        "confidence_score": confidence,
        "confidence_level": _confidence_label(confidence) if confidence is not None else None,
        "urgency_level": result.urgency,
        "requires_expert_review": requires_expert,
        "top_predictions": [
            {
                "rank": i + 1,
                "class_label": p.label,
                "name_bn": p.name_bn,
                "name_en": p.name_en,
                "confidence_score": p.confidence,
            }
            for i, p in enumerate(result.predictions)
        ],
        "advisory": advisory,
        "notice_bn": notice_bn,
        "engine": ENGINE_ID,
        "from_cache": from_cache,
        "saved_as_case": False,
    }


# ─────────────────────────────────────────────────────────
# Route
# ─────────────────────────────────────────────────────────
@router.post("/quick-diagnosis", summary="Upload a crop photo and get the diagnosis in one call")
async def quick_diagnosis(
    request: Request,
    image: UploadFile = File(..., description="Crop / leaf photo (jpg, png, webp; max 5 MB)"),
    crop_name: Optional[str] = Form(None, max_length=60),
    notes: Optional[str] = Form(None, max_length=300),
    current_user: User = Depends(require_roles("farmer", "agent")),
):
    if image.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail={"code": "UNSUPPORTED_IMAGE_TYPE", "message_bn": "শুধু JPG, PNG বা WEBP ছবি আপলোড করা যাবে।"},
        )

    raw = await image.read(MAX_UPLOAD_BYTES + 1)
    if not raw:
        raise HTTPException(
            status_code=400,
            detail={"code": "EMPTY_IMAGE", "message_bn": "ছবির ফাইলটি খালি।"},
        )
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail={"code": "IMAGE_TOO_LARGE", "message_bn": "ছবির সাইজ ৫ এমবির বেশি হতে পারবে না।"},
        )

    key = _cache_key(raw, crop_name)

    # 1) cache hit  -> free
    result = _cache.get(key)
    from_cache = result is not None

    if result is None:
        # 2) same photo already being diagnosed (double tap / retry) -> join it, free
        task = _inflight.get(key)
        if task is None:
            # 3) genuinely new photo -> the only path that costs money
            _enforce_limits(current_user, request)
            task = asyncio.create_task(_diagnose_and_cache(key, raw, crop_name, notes))
            _inflight[key] = task
            task.add_done_callback(lambda _t, k=key: _inflight.pop(k, None))
        try:
            # shield: if the client disconnects, the paid call still finishes and gets cached
            result = await asyncio.shield(task)
        except InvalidImageError:
            raise HTTPException(
                status_code=400,
                detail={"code": "INVALID_IMAGE", "message_bn": "ছবিটি পড়া যায়নি। অন্য একটি ছবি দিয়ে চেষ্টা করুন।"},
            )
        except EngineError as exc:
            logger.warning("quick diagnosis engine failure: %s", exc)
            raise HTTPException(
                status_code=502,
                detail={"code": "DIAGNOSIS_FAILED", "message_bn": "বিশ্লেষণ করা যায়নি। কিছুক্ষণ পর আবার চেষ্টা করুন।"},
            )

    if not result.is_crop_image:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "NOT_A_CROP_IMAGE",
                "message_bn": "ছবিতে ফসল বা গাছের পাতা শনাক্ত হয়নি। কাছ থেকে পরিষ্কার ছবি তুলুন।",
            },
        )

    return success_response(
        data=_build_payload(result, from_cache),
        message="বিশ্লেষণ সম্পন্ন হয়েছে।",
    )
