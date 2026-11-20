"""
app/services/diagnosis_engine.py
================================
THE ONLY FILE you replace when you build your own model.

The router (api/v1/quick_diagnosis.py) depends on exactly these names:

    ENGINE_ID                         str   -> used in cache key + response meta
    InvalidImageError                 bad / unreadable image   (router -> 400)
    EngineError                       model / API failure      (router -> 502)
    Prediction, EngineResult          return types
    async diagnose(image_bytes, *, crop_hint=None, notes=None) -> EngineResult

Default implementation below = vision LLM over HTTPS (Anthropic Messages API)
with cost guards:
  * photo is downscaled + re-encoded as JPEG BEFORE sending (fewer input tokens)
  * output is capped (MAX_OUTPUT_TOKENS) and Bangla fields are kept short
  * temperature 0, NO automatic retry (a retry = a second paid call)
  * token usage is logged on every call so you can watch the bill

Other provider (Gemini / OpenAI)?  Change only `_call_vision_api`.
Your own model?  See the TEMPLATE at the bottom of this file.

Env vars:
  ANTHROPIC_API_KEY          required for the default engine
  DIAGNOSIS_MODEL            default "claude-haiku-5-5" (cheapest tier)
  DIAGNOSIS_MAX_SIDE_PX      default 800
"""
from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import os
from dataclasses import dataclass, field

import httpx
from PIL import Image, ImageOps, UnidentifiedImageError

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────
API_URL = "https://api.anthropic.com/v1/messages"
MODEL = os.getenv("DIAGNOSIS_MODEL", "claude-haiku-5-5")
ENGINE_ID = f"vision-llm:{MODEL}"

MAX_SIDE_PX = int(os.getenv("DIAGNOSIS_MAX_SIDE_PX", "800"))  # smaller = cheaper
JPEG_QUALITY = 80
MAX_OUTPUT_TOKENS = 600
REQUEST_TIMEOUT_S = 30


# ─────────────────────────────────────────────────────────
# Contract (keep these when you swap the engine)
# ─────────────────────────────────────────────────────────
class InvalidImageError(ValueError):
    """The uploaded bytes are not a readable image."""


class EngineError(RuntimeError):
    """The model / API failed or returned something unusable."""


@dataclass
class Prediction:
    label: str                   # stable class label, e.g. "rice_blast" or "healthy"
    confidence: float            # 0.0 - 1.0
    name_bn: str | None = None
    name_en: str | None = None


@dataclass
class EngineResult:
    is_crop_image: bool
    predictions: list[Prediction] = field(default_factory=list)  # best first
    urgency: str = "medium"      # "low" | "medium" | "high"
    crop: str | None = None
    summary_bn: str = ""
    treatment_bn: str = ""
    prevention_bn: str = ""


# ─────────────────────────────────────────────────────────
# Default engine: vision LLM
# ─────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a crop disease triage assistant for smallholder farmers in Bangladesh.
Look at the photo and reply with ONE JSON object and nothing else (no markdown, no comments).

Schema:
{"is_crop_image": true, "crop": "rice", "predictions": [{"label": "rice_blast", "name_en": "Rice blast", "name_bn": "ধানের ব্লাস্ট", "confidence": 0.82}], "urgency": "medium", "summary_bn": "...", "treatment_bn": "...", "prevention_bn": "..."}

Rules:
- predictions: max 3, best first. Use label "healthy" when the plant looks healthy.
- confidence is 0 to 1. Lower it when the photo is blurry, dark, or shows only a small part of the plant.
- urgency is one of "low", "medium", "high".
- summary_bn: Bangla, max 2 short sentences. treatment_bn: Bangla, max 3 short sentences. prevention_bn: Bangla, max 2 short sentences.
- NEVER mention pesticide or chemical names, doses or mixing ratios. Give only general cultural/organic steps and tell the farmer to confirm treatment with a local agriculture officer.
- If the photo is not a plant/crop/leaf/fruit: is_crop_image=false, predictions=[], and empty strings for the Bangla fields."""


def _user_text(crop_hint: str | None, notes: str | None) -> str:
    parts = ["Diagnose this crop photo."]
    if crop_hint:
        parts.append(f"Farmer says the crop is: {crop_hint[:60]}.")
    if notes:
        parts.append(f"Farmer notes: {notes[:300]}")
    return " ".join(parts)


def _prepare_image(raw: bytes) -> tuple[bytes, str]:
    """Validate + shrink the photo. Fewer pixels -> fewer input tokens -> lower cost."""
    try:
        img = Image.open(io.BytesIO(raw))
        img = ImageOps.exif_transpose(img)   # phone photos: respect rotation
        img = img.convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise InvalidImageError("unreadable image") from exc

    img.thumbnail((MAX_SIDE_PX, MAX_SIDE_PX))  # keeps aspect ratio, never upscales
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return buf.getvalue(), "image/jpeg"


async def _call_vision_api(b64_image: str, media_type: str, user_text: str) -> str:
    """Provider-specific part. Uses Google Gemini Vision (or Anthropic if configured)."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    # 1. Use Google GenAI (Gemini) if GEMINI_API_KEY is configured
    if gemini_key and not anthropic_key:
        try:
            from google import genai
            from google.genai import types as genai_types

            client = genai.Client(api_key=gemini_key)
            g_model = os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
            raw_bytes = base64.b64decode(b64_image)

            def _call_gemini():
                return client.models.generate_content(
                    model=g_model,
                    contents=[
                        genai_types.Part.from_bytes(data=raw_bytes, mime_type=media_type),
                        f"{SYSTEM_PROMPT}\n\nTask: {user_text}",
                    ],
                )

            resp = await asyncio.to_thread(_call_gemini)
            return resp.text or "{}"
        except Exception as exc:
            raise EngineError(f"Gemini Vision API call failed: {exc}") from exc

    # 2. Fallback to Anthropic Claude Vision
    if not anthropic_key:
        raise EngineError("Neither GEMINI_API_KEY nor ANTHROPIC_API_KEY is set")

    body = {
        "model": MODEL,
        "max_tokens": MAX_OUTPUT_TOKENS,
        "temperature": 0,
        "system": SYSTEM_PROMPT,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64_image}},
                {"type": "text", "text": user_text},
            ],
        }],
    }
    headers = {
        "x-api-key": anthropic_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S) as client:
            resp = await client.post(API_URL, headers=headers, json=body)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise EngineError(f"vision API call failed: {exc}") from exc

    data = resp.json()
    usage = data.get("usage", {})
    logger.info(
        "diagnosis api usage model=%s input_tokens=%s output_tokens=%s",
        MODEL, usage.get("input_tokens"), usage.get("output_tokens"),
    )
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")


def _extract_json(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise EngineError("model returned no JSON")
    try:
        data = json.loads(text[start:end + 1])
    except json.JSONDecodeError as exc:
        raise EngineError("model returned invalid JSON") from exc
    if not isinstance(data, dict):
        raise EngineError("model returned unexpected JSON shape")
    return data


def _to_result(data: dict) -> EngineResult:
    preds: list[Prediction] = []
    for p in (data.get("predictions") or [])[:3]:
        if not isinstance(p, dict):
            continue
        label = str(p.get("label") or "").strip()
        try:
            conf = max(0.0, min(1.0, float(p.get("confidence", 0))))
        except (TypeError, ValueError):
            continue
        if not label:
            continue
        preds.append(Prediction(label=label, confidence=conf,
                                name_bn=p.get("name_bn"), name_en=p.get("name_en")))
    preds.sort(key=lambda x: x.confidence, reverse=True)

    urgency = data.get("urgency")
    return EngineResult(
        is_crop_image=bool(data.get("is_crop_image", True)),
        predictions=preds,
        urgency=urgency if urgency in ("low", "medium", "high") else "medium",
        crop=data.get("crop"),
        summary_bn=str(data.get("summary_bn") or ""),
        treatment_bn=str(data.get("treatment_bn") or ""),
        prevention_bn=str(data.get("prevention_bn") or ""),
    )


async def diagnose(
    image_bytes: bytes,
    *,
    crop_hint: str | None = None,
    notes: str | None = None,
) -> EngineResult:
    """The one function the router calls."""
    jpeg, media_type = await asyncio.to_thread(_prepare_image, image_bytes)
    b64 = base64.b64encode(jpeg).decode()
    text = await _call_vision_api(b64, media_type, _user_text(crop_hint, notes))
    return _to_result(_extract_json(text))


# ─────────────────────────────────────────────────────────
# TEMPLATE: your own model (PyTorch / ONNX / TensorFlow)
# ─────────────────────────────────────────────────────────
# Delete the LLM parts above (httpx, SYSTEM_PROMPT, _call_vision_api, _extract_json,
# _to_result) and keep: ENGINE_ID, the two exceptions, the two dataclasses, `diagnose`.
#
#   ENGINE_ID = "chashiguard-cnn-v1"
#   _model = load_model("models/chashiguard.onnx")      # load ONCE at import time
#   CLASSES = [("rice_blast", "Rice blast", "ধানের ব্লাস্ট"), ...]
#
#   async def diagnose(image_bytes, *, crop_hint=None, notes=None) -> EngineResult:
#       try:
#           tensor = await asyncio.to_thread(preprocess, image_bytes)  # raise InvalidImageError if bad
#           probs = await asyncio.to_thread(_model.predict, tensor)
#       except InvalidImageError:
#           raise
#       except Exception as exc:
#           raise EngineError(str(exc)) from exc
#       top3 = probs.argsort()[::-1][:3]
#       return EngineResult(
#           is_crop_image=True,
#           predictions=[Prediction(CLASSES[i][0], float(probs[i]), CLASSES[i][2], CLASSES[i][1])
#                        for i in top3],
#           urgency="medium",
#           summary_bn="...", treatment_bn="...", prevention_bn="...",  # can come from your Advisory table
#       )
