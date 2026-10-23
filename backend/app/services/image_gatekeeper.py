"""
backend/app/services/image_gatekeeper.py
=========================================
Strict Agricultural Image Verification Gatekeeper Service.

Inspects uploaded crop images using Gemini Vision to verify if:
1. It is a genuine crop/plant image (not a selfie, document, animal, car, etc.).
2. The detected crop matches the user's selected crop and is available in the system catalog.
3. Automatically auto-selects if the user selected the wrong crop but provided a valid system crop.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    import google.genai as genai
    from google.genai import types as genai_types
except ImportError:
    genai = None
    genai_types = None

from app.core.config import settings
from app.models.catalog import Crop

logger = logging.getLogger("krishibondhu.gatekeeper")

# Bengali crop name mapping
CROP_BN_NAMES: Dict[str, str] = {
    "potato": "আলু",
    "tomato": "টমেটো",
    "chili": "মরিচ",
    "rice": "ধান",
    "wheat": "গম",
    "maize": "ভুট্টা",
    "brinjal": "বেগুন",
    "jute": "পাট",
    "mango": "আম",
    "onion": "পেঁয়াজ",
    "garlic": "রসুন",
}


class VerificationResult(BaseModel):
    is_crop: bool
    detected_crop: str
    is_available: bool
    is_user_selection_correct: bool
    auto_selected: bool
    action_status: str  # REJECT_NOT_CROP | REJECT_NOT_AVAILABLE | VALID_MATCH | VALID_AUTO_SELECTED
    final_selected_crop: Optional[str] = None
    message_bn: str


async def get_system_available_crops(db: AsyncSession) -> List[str]:
    """Fetch active crop codes directly from catalog.crops database table."""
    result = await db.execute(select(Crop.code).where(Crop.is_active == True))
    return [row[0].lower().strip() for row in result.fetchall()]


async def verify_crop_image_gatekeeper(
    gemini_client: Optional[Any],
    image_bytes: bytes,
    mime_type: str,
    selected_crop: str,
    available_crops: List[str],
    model_name: str = "gemini-1.5-flash",
) -> VerificationResult:
    """
    Agricultural Image Verification Gatekeeper using Google Gemini Vision.
    """
    normalized_selected = selected_crop.lower().strip() if selected_crop else "potato"

    prompt = f"""You are a strict Agricultural Image Verification Gatekeeper.
Your ONLY job is to inspect the uploaded image and verify whether it is a valid crop/plant image and match it against the user's selected crop and the system's available crops list.

INPUT VARIABLES:
- User Selected Crop: "{normalized_selected}"
- System Available Crops List: {json.dumps(available_crops)}

FOLLOW THESE EXACT STEP-BY-STEP RULES:

STEP 1: CHECK IMAGE QUALITY & VALIDITY (IS IT A CROP?)
- Inspect if the image clearly shows a crop, plant, leaf, stem, fruit, vegetable, or agricultural field.
- If the image shows a human selfie, animal, car, indoor room, random object, screenshot, text document, or is completely blurry/dark/unrecognizable:
  -> Set "is_crop": false
  -> Set "action_status": "REJECT_NOT_CROP"
  -> Set "detected_crop": "none"
  -> Set "final_selected_crop": null
  -> Set "message_bn": "এটি কোনো ফসলের ছবি নয় বা ছবিটি স্পষ্ট নয়। অনুগ্রহ করে ফসলের পাতার পরিষ্কার ছবি তুলে আবার আপলোড করুন।"

STEP 2: IDENTIFY THE CROP & SYNONYM NORMALIZATION
- If "is_crop" is true, identify the exact crop name in lowercase singular English (e.g. potato, tomato, chili, rice, wheat, maize, brinjal, jute, mango).
- Normalize common synonyms:
  * "alu" -> "potato"
  * "morich" or "chilli" or "pepper" -> "chili"
  * "paddy" or "dhan" -> "rice"
  * "begun" or "eggplant" -> "brinjal"
  * "bhutta" or "corn" -> "maize"
  * "gom" -> "wheat"

STEP 3: CHECK AVAILABILITY IN SYSTEM LIST
- Check if "detected_crop" exists in System Available Crops List: {json.dumps(available_crops)}.
- CASE A (NOT AVAILABLE): If "detected_crop" is NOT in {json.dumps(available_crops)}:
  -> Set "is_available": false
  -> Set "action_status": "REJECT_NOT_AVAILABLE"
  -> Set "final_selected_crop": null
  -> Set "message_bn": "আপনি [detected_crop-এর বাংলা নাম]-এর ছবি দিয়েছেন, কিন্তু এই ফসলটি বর্তমানে আমাদের সিস্টেমে নেই (Not Available)।"

STEP 4: COMPARE WITH USER SELECTION & AUTO-SELECT
- CASE B (EXACT MATCH): If "detected_crop" IS in {json.dumps(available_crops)} AND matches "{normalized_selected}":
  -> Set "is_available": true
  -> Set "is_user_selection_correct": true
  -> Set "auto_selected": false
  -> Set "action_status": "VALID_MATCH"
  -> Set "final_selected_crop": "{normalized_selected}"
  -> Set "message_bn": "ফসলের ছবিটি সঠিক আছে।"

- CASE C (MISMATCH -> AUTO-SELECT): If "detected_crop" IS in {json.dumps(available_crops)} BUT does NOT match "{normalized_selected}":
  -> Set "is_available": true
  -> Set "is_user_selection_correct": false
  -> Set "auto_selected": true
  -> Set "action_status": "VALID_AUTO_SELECTED"
  -> Set "final_selected_crop": "<detected_crop>"
  -> Set "message_bn": "আপনি ভুল ফসল সিলেক্ট করেছিলেন। ছবি দেখে স্বয়ংক্রিয়ভাবে '[detected_crop-এর বাংলা নাম]' সিলেক্ট করা হয়েছে।"

OUTPUT FORMAT:
Return ONLY a valid JSON object matching this schema without markdown or code fences:
{{
  "is_crop": boolean,
  "detected_crop": string,
  "is_available": boolean,
  "is_user_selection_correct": boolean,
  "auto_selected": boolean,
  "action_status": string,
  "final_selected_crop": string or null,
  "message_bn": string
}}
"""

    if not gemini_client or not genai_types:
        # Fallback if Gemini client is not configured
        is_avail = normalized_selected in available_crops
        return VerificationResult(
            is_crop=True,
            detected_crop=normalized_selected,
            is_available=is_avail,
            is_user_selection_correct=True,
            auto_selected=False,
            action_status="VALID_MATCH" if is_avail else "REJECT_NOT_AVAILABLE",
            final_selected_crop=normalized_selected if is_avail else None,
            message_bn="ফসলের ছবিটি সঠিক আছে।" if is_avail else f"নির্বাচিত ফসলটি সিস্টেমে নেই।",
        )

    try:
        response = gemini_client.models.generate_content(
            model=model_name,
            contents=[
                prompt,
                genai_types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            ],
            config=genai_types.GenerateContentConfig(
                temperature=0.0,
                max_output_tokens=512,
            ),
        )

        clean_text = response.text.strip()
        if clean_text.startswith("```"):
            clean_text = clean_text.split("```")[1]
            if clean_text.startswith("json"):
                clean_text = clean_text[4:]
            clean_text = clean_text.strip()

        data = json.loads(clean_text)
        return VerificationResult(**data)

    except Exception as exc:
        logger.error(f"Image gatekeeper validation failed: {exc}")
        # Safe fallback in case of AI communication failure
        is_avail = normalized_selected in available_crops
        return VerificationResult(
            is_crop=True,
            detected_crop=normalized_selected,
            is_available=is_avail,
            is_user_selection_correct=True,
            auto_selected=False,
            action_status="VALID_MATCH" if is_avail else "REJECT_NOT_AVAILABLE",
            final_selected_crop=normalized_selected if is_avail else None,
            message_bn="ফসলের ছবিটি সঠিক আছে।" if is_avail else "নির্বাচিত ফসলটি সিস্টেমে নেই।",
        )
