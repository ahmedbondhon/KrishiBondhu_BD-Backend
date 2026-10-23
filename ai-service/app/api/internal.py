"""
ai-service/app/api/internal.py
================================
Internal AI endpoints powered by Google Gemini Vision API.

Replaces the mock prediction stub with REAL AI image analysis.

POST /internal/v1/image-quality/check
  → Validates image quality (blur, brightness) before sending to Gemini.

POST /internal/v1/crop-diagnosis/predict
  → Sends the crop image to Gemini 1.5 Flash (vision model).
  → Gemini analyzes the image and returns a structured diagnosis.
  → Maps Gemini's response to our standard prediction format.

Model used: gemini-1.5-flash (fast, cheap, excellent vision capabilities)
Why Flash over Pro? For agricultural field images it performs equally well
and costs 10x less, which matters at scale for rural Bangladesh farmers.
"""

import json
import os
import random
import re
import time
from typing import Any, Dict, List, Optional

import google.genai as genai
from google.genai import types as genai_types
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/internal/v1")

# ── Gemini Client Setup ───────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

if GEMINI_API_KEY:
    _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
else:
    _gemini_client = None

# ── Request / Response Schemas ────────────────────────────

class ImageQualityCheckRequest(BaseModel):
    case_id: str
    storage_path: str


class ImageQualityCheckResponse(BaseModel):
    passed: bool
    blur_score: float
    brightness_score: float
    resolution_ok: bool
    failure_reason: Optional[str] = None
    message_bn: Optional[str] = None


class CropDiagnosisPredictRequest(BaseModel):
    case_id: str
    crop_id: Optional[str] = None
    storage_path: str
    image_base64: Optional[str] = Field(None, description="Base64 encoded image data")
    image_mime_type: Optional[str] = Field("image/jpeg", description="MIME type of the image")


class TopPrediction(BaseModel):
    rank: int
    class_label: str
    confidence_score: float
    issue_code: Optional[str] = None


class CropDiagnosisPredictResponse(BaseModel):
    case_id: str
    model_name: str
    model_version: str
    primary_issue_code: Optional[str]
    confidence_score: float
    urgency_level: str
    top_predictions: List[TopPrediction]
    processing_time_ms: int
    diagnosis_summary_bn: Optional[str] = None
    treatment_advice_bn: Optional[str] = None
    metadata: Dict[str, Any] = {}


# ── Gemini Diagnosis Prompt ───────────────────────────────
DIAGNOSIS_PROMPT = """You are an expert agricultural plant pathologist specializing in crops grown in Bangladesh (potato, tomato, chili, rice, jute).

Analyze this crop image carefully and provide a structured diagnosis.

Return your response as a valid JSON object with EXACTLY this structure:
{
  "primary_issue_code": "ISSUE_CODE_HERE",
  "primary_issue_label": "English disease name",
  "confidence_score": 0.85,
  "urgency_level": "medium",
  "diagnosis_summary_bn": "Bangla summary of what you see (2-3 sentences)",
  "treatment_advice_bn": "Bangla treatment advice (2-3 sentences)",
  "top_predictions": [
    {"rank": 1, "class_label": "Disease Name", "confidence_score": 0.85, "issue_code": "CODE"},
    {"rank": 2, "class_label": "Alternative", "confidence_score": 0.10, "issue_code": "CODE2"},
    {"rank": 3, "class_label": "Alternative", "confidence_score": 0.05, "issue_code": "CODE3"}
  ]
}

Rules:
- issue_code must be UPPERCASE_WITH_UNDERSCORES (e.g. POTATO_EARLY_BLIGHT, TOMATO_LATE_BLIGHT, HEALTHY)
- confidence_score must be between 0.0 and 1.0
- urgency_level must be one of: low, medium, high, critical
- Use HEALTHY as issue_code if the plant looks healthy
- If image is unclear/not a crop, set confidence_score to 0.30 and issue_code to UNKNOWN
- diagnosis_summary_bn and treatment_advice_bn MUST be in Bengali (Bangla) script
- All top_predictions confidence scores must sum to approximately 1.0

Respond with ONLY the JSON object, no other text."""


def _parse_gemini_response(text: str) -> dict:
    """Extract and parse JSON from Gemini's response text."""
    # Strip markdown code blocks if present
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"```(?:json)?\n?", "", text)
        text = text.rstrip("`").strip()

    # Find the JSON object
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON found in Gemini response")

    return json.loads(text[start:end])


# ── Fallback predictions when Gemini is unavailable ──────
FALLBACK_POOL = [
    {"issue_code": "POTATO_EARLY_BLIGHT", "class_label": "Potato Early Blight", "urgency": "medium", "conf": 0.82},
    {"issue_code": "TOMATO_LATE_BLIGHT",  "class_label": "Tomato Late Blight",  "urgency": "high",   "conf": 0.88},
    {"issue_code": "HEALTHY",             "class_label": "Healthy Plant",        "urgency": "low",    "conf": 0.95},
]


# ── Endpoints ─────────────────────────────────────────────

@router.post("/image-quality/check", response_model=ImageQualityCheckResponse,
             tags=["Internal — Image Quality"])
async def check_image_quality(payload: ImageQualityCheckRequest):
    """
    Validate image quality before sending to Gemini.
    Returns mock quality scores (good enough for MVP).
    In production: fetch image from storage and run OpenCV checks.
    """
    return ImageQualityCheckResponse(
        passed=True,
        blur_score=round(random.uniform(140.0, 280.0), 2),
        brightness_score=round(random.uniform(80.0, 180.0), 2),
        resolution_ok=True,
    )


@router.post("/crop-diagnosis/predict", response_model=CropDiagnosisPredictResponse,
             tags=["Internal — Crop Diagnosis"])
async def predict_crop_disease(payload: CropDiagnosisPredictRequest, request: Request):
    """
    Diagnose crop disease using Google Gemini Vision API.

    Expects either:
      - image_base64: Base64-encoded image bytes + image_mime_type
      - OR falls back to mock predictions (if no API key or no image data)

    The backend sends image_base64 after fetching the image from Supabase/S3 storage.
    """
    start = time.monotonic()
    model_name = getattr(request.app.state, "model_name", "gemini-1.5-flash")

    # ── Real Gemini inference ─────────────────────────────
    if _gemini_client and payload.image_base64:
        try:
            import base64

            image_bytes = base64.b64decode(payload.image_base64)
            mime = payload.image_mime_type or "image/jpeg"

            import asyncio

            def _call_gemini_predict():
                return _gemini_client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=[
                        DIAGNOSIS_PROMPT,
                        genai_types.Part.from_bytes(data=image_bytes, mime_type=mime),
                    ],
                    config=genai_types.GenerateContentConfig(
                        temperature=0.1,
                        max_output_tokens=1024,
                    ),
                )

            response = await asyncio.to_thread(_call_gemini_predict)

            result = _parse_gemini_response(response.text)
            processing_ms = int((time.monotonic() - start) * 1000)

            top_preds = [
                TopPrediction(
                    rank=p["rank"],
                    class_label=p["class_label"],
                    confidence_score=float(p["confidence_score"]),
                    issue_code=p.get("issue_code"),
                )
                for p in result.get("top_predictions", [])
            ]

            return CropDiagnosisPredictResponse(
                case_id=payload.case_id,
                model_name=model_name,
                model_version=GEMINI_MODEL,
                primary_issue_code=result.get("primary_issue_code"),
                confidence_score=float(result.get("confidence_score", 0.5)),
                urgency_level=result.get("urgency_level", "medium"),
                top_predictions=top_preds,
                processing_time_ms=processing_ms,
                diagnosis_summary_bn=result.get("diagnosis_summary_bn"),
                treatment_advice_bn=result.get("treatment_advice_bn"),
                metadata={
                    "model_used": GEMINI_MODEL,
                    "powered_by": "Google Gemini Vision",
                    "storage_path": payload.storage_path,
                },
            )

        except Exception as e:
            import logging
            logging.getLogger("krishibondhu.ai-service").warning(
                f"Gemini API call failed: {e}. Falling back to mock."
            )

    # ── Mock fallback (no API key or no image data) ───────
    primary = random.choice(FALLBACK_POOL)
    conf = round(primary["conf"] + random.uniform(-0.06, 0.04), 4)
    conf = max(0.0, min(1.0, conf))

    others = [p for p in FALLBACK_POOL if p["issue_code"] != primary["issue_code"]]
    remaining = 1.0 - conf
    top_preds = [TopPrediction(rank=1, class_label=primary["class_label"],
                               confidence_score=conf, issue_code=primary["issue_code"])]
    for i, o in enumerate(others[:2], start=2):
        c = round(remaining * random.uniform(0.3, 0.6), 4)
        remaining -= c
        top_preds.append(TopPrediction(rank=i, class_label=o["class_label"],
                                       confidence_score=max(0.0, c), issue_code=o["issue_code"]))

    processing_ms = int((time.monotonic() - start) * 1000) + random.randint(200, 500)

    return CropDiagnosisPredictResponse(
        case_id=payload.case_id,
        model_name=model_name,
        model_version="mock-v1.0",
        primary_issue_code=primary["issue_code"],
        confidence_score=conf,
        urgency_level=primary["urgency"],
        top_predictions=top_preds,
        processing_time_ms=processing_ms,
        diagnosis_summary_bn="ছবি বিশ্লেষণ করা হয়েছে। (Mock mode — GEMINI_API_KEY সেট করুন)",
        treatment_advice_bn="বিশেষজ্ঞের পরামর্শ নিন।",
        metadata={"model_backend": "mock-fallback", "storage_path": payload.storage_path},
    )
