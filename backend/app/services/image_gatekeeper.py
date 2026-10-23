"""
backend/app/services/image_gatekeeper.py
=========================================
Strict Agricultural Image Verification Gatekeeper Service.

Inspects uploaded crop images using Gemini Vision (or local Computer Vision heuristics) to verify:
1. It is a genuine crop/plant image (not a selfie, document, animal, car, etc.).
2. The detected crop matches the user's selected crop and is available in the system catalog.
3. Automatically auto-selects if the user selected the wrong crop but provided a valid system crop.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path so the script can run directly or as a module
backend_dir = str(Path(__file__).resolve().parent.parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    genai = None  # type: ignore
    genai_types = None  # type: ignore

from app.core.config import settings
from app.models.catalog import Crop

logger = logging.getLogger("krishibondhu.gatekeeper")

# MVP Pilot Target Crops
PILOT_CROPS: List[str] = ["potato", "tomato", "chili"]

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

# Synonym normalization map
CROP_SYNONYMS: Dict[str, str] = {
    "alu": "potato",
    "potatoes": "potato",
    "morich": "chili",
    "chilli": "chili",
    "chillies": "chili",
    "pepper": "chili",
    "hot pepper": "chili",
    "capsicum": "chili",
    "tomatoes": "tomato",
    "paddy": "rice",
    "dhan": "rice",
    "begun": "brinjal",
    "eggplant": "brinjal",
    "aubergine": "brinjal",
    "bhutta": "maize",
    "corn": "maize",
    "gom": "wheat",
}


class RawAIVisionOutput(BaseModel):
    is_crop: bool
    is_clear_image: bool
    detected_crop: str        # e.g., "potato", "tomato", "chili", "none"
    detected_crop_bn: str     # e.g., "আলু", "টমেটো", "মরিচ", "অজ্ঞাত"


class VerificationResult(BaseModel):
    is_crop: bool
    detected_crop: str
    is_available: bool
    is_user_selection_correct: bool
    auto_selected: bool
    action_status: str  # REJECT_NOT_CROP | REJECT_NOT_AVAILABLE | VALID_MATCH | VALID_AUTO_SELECTED
    final_selected_crop: Optional[str] = None
    message_bn: str


def get_gemini_client() -> Optional[Any]:
    """Instantiate Google GenAI Client if API key is configured."""
    api_key = (
        os.getenv("GEMINI_API_KEY", "")
        or getattr(settings, "GEMINI_API_KEY", "")
        or getattr(settings, "gemini_api_key", "")
    )
    if not api_key:
        return None

    if genai:
        try:
            return genai.Client(api_key=api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Google GenAI Client: {e}")
    return None


async def get_system_available_crops(db: AsyncSession) -> List[str]:
    """Fetch active crop codes directly from catalog.crops database table."""
    try:
        result = await db.execute(select(Crop.code).where(Crop.is_active == True))
        crops = [row[0].lower().strip() for row in result.fetchall()]
        return crops if crops else PILOT_CROPS
    except Exception as exc:
        logger.warning(f"Could not load crops from database, using PILOT_CROPS fallback: {exc}")
        return PILOT_CROPS


def normalize_crop_name(name: str) -> str:
    """Normalize crop name and resolve synonyms."""
    clean = name.lower().strip()
    return CROP_SYNONYMS.get(clean, clean)


def _inspect_image_heuristic(image_bytes: bytes) -> tuple[bool, str, Optional[str]]:
    """
    Computer vision inspection using PyMuPDF and NumPy.
    Detects human skin tones (selfies, human faces, bodies), documents,
    indoor objects, and verifies agricultural plant chlorophyll/foliage.

    Returns:
        (is_crop: bool, classification_reason: str, detected_crop: Optional[str])
    """
    try:
        import pymupdf
        import numpy as np

        pix = pymupdf.Pixmap(image_bytes)
        if pix.n < 3 or pix.alpha:
            pix = pymupdf.Pixmap(pymupdf.csRGB, pix)

        arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
        h, w, _ = arr.shape
        N = h * w
        if N == 0:
            return False, "EMPTY_IMAGE", None

        R = arr[:, :, 0].astype(float)
        G = arr[:, :, 1].astype(float)
        B = arr[:, :, 2].astype(float)

        # 1. Human skin detection (face, selfie, portrait, hand)
        # Standard RGB rule: R > 95, G > 40, B > 20, R > G > B, max-min > 15, R-G > 12
        skin_mask = (
            (R > 95)
            & (G > 40)
            & (B > 20)
            & ((R - G) > 12)
            & (R > G)
            & (R > B)
            & ((np.maximum(R, np.maximum(G, B)) - np.minimum(R, np.minimum(G, B))) > 15)
        )
        skin_ratio = np.count_nonzero(skin_mask) / N

        # 2. Vegetation / Plant foliage (Excess Green Index: ExG = 2*G - R - B)
        exg = 2 * G - R - B
        foliage_mask = (G > R * 0.95) & (G > B) & (exg > 5) & (G > 30)
        foliage_ratio = np.count_nonzero(foliage_mask) / N

        # 3. Red/Orange harvest (Tomato, ripe chili)
        red_crop_mask = (R > 130) & (R > G * 1.3) & (R > B * 1.4)
        red_crop_ratio = np.count_nonzero(red_crop_mask) / N

        # 4. Earthy/Tuber harvest (Potato tubers, brown/tan soil with harvest)
        potato_mask = (R > 100) & (G > 80) & (B < 110) & (R >= G) & ((R - G) < 35) & (G > B * 1.15)
        potato_ratio = np.count_nonzero(potato_mask) / N

        # Decision rules
        if skin_ratio > 0.12 and foliage_ratio < 0.08:
            return False, "HUMAN_SELFIE", None

        if skin_ratio > 0.08 and foliage_ratio < 0.04:
            return False, "HUMAN_SELFIE", None

        total_agricultural = foliage_ratio + red_crop_ratio + potato_ratio
        if total_agricultural < 0.04:
            # Document, blank wall, screenshot, car, furniture
            return False, "NO_PLANT_DETECTED", None

        # Determine likely crop from dominant features
        predicted = "potato"
        if red_crop_ratio > foliage_ratio and red_crop_ratio > 0.15:
            predicted = "tomato"
        elif foliage_ratio > 0.08:
            predicted = "potato"
        elif potato_ratio > 0.15:
            predicted = "potato"

        return True, "VALID_CROP", predicted

    except Exception as e:
        logger.warning(f"Heuristic image inspection failed: {e}")
        return False, "INSPECTION_ERROR", None


async def verify_crop_image_gatekeeper(
    gemini_client: Optional[Any],
    image_bytes: bytes,
    mime_type: str,
    selected_crop: str,
    available_crops: Optional[List[str]] = None,
    model_name: str = "gemini-1.5-flash",
) -> VerificationResult:
    """
    Strict Agricultural Image Verification Gatekeeper.
    Uses Google Gemini Vision if available, with intelligent Computer Vision
    heuristics fallback to reject selfies and non-crop photos.
    """
    if not available_crops:
        available_crops = PILOT_CROPS
    else:
        available_crops = [normalize_crop_name(c) for c in available_crops]

    normalized_selected = normalize_crop_name(selected_crop) if selected_crop else "potato"

    if gemini_client is None:
        gemini_client = get_gemini_client()

    ai_out: Optional[RawAIVisionOutput] = None

    # Step 1: Attempt Gemini Vision API if client is available
    if gemini_client and genai_types:
        prompt = """
        You are a strict Agricultural Image Verification Gatekeeper.
        Carefully inspect the uploaded image:
        1. Is it a genuine, clearly visible photograph of an agricultural crop, plant, leaf, stem, fruit, or vegetable?
           - If the image shows a human person/selfie, animal, vehicle, room, furniture, computer screen, screenshot, document, cartoon, or random object -> set is_crop = false, detected_crop = "none", detected_crop_bn = "অজ্ঞাত".
           - If the image is completely blurry, pitch dark, or unrecognizable -> set is_clear_image = false, is_crop = false, detected_crop = "none".
        2. If it IS a genuine plant/crop image:
           - Set is_crop = true and is_clear_image = true.
           - Set detected_crop to the specific lowercase singular English crop name (e.g., "potato", "tomato", "chili", "rice", "brinjal", "mango", "wheat", "maize").
           - Set detected_crop_bn to its common Bengali name (e.g., "আলু", "টমেটো", "মরিচ", "ধান", "বেগুন", "আম").
        """
        try:
            def _call_gemini_sync():
                return gemini_client.models.generate_content(
                    model=model_name,
                    contents=[
                        genai_types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                        prompt,
                    ],
                    config=genai_types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=RawAIVisionOutput,
                        temperature=0.0,
                    ),
                )

            response = await asyncio.to_thread(_call_gemini_sync)
            ai_out = RawAIVisionOutput.model_validate_json(response.text)
        except Exception as exc:
            logger.warning(f"Gemini Vision call failed, switching to Computer Vision heuristic: {exc}")

    # Step 2: Fallback to Computer Vision heuristic analysis if Gemini wasn't available or failed
    if ai_out is None:
        is_plant, reason, predicted_crop = _inspect_image_heuristic(image_bytes)
        if not is_plant:
            if reason == "HUMAN_SELFIE":
                return VerificationResult(
                    is_crop=False,
                    detected_crop="none",
                    is_available=False,
                    is_user_selection_correct=False,
                    auto_selected=False,
                    action_status="REJECT_NOT_CROP",
                    final_selected_crop=None,
                    message_bn="এটি কোনো ফসলের ছবি নয় (মানুষের ছবি বা সেলফি সনাক্ত হয়েছে)। অনুগ্রহ করে শুধুমাত্র আক্রান্ত ফসলের পাতার পরিষ্কার ছবি তুলে আপলোড করুন।",
                )
            else:
                return VerificationResult(
                    is_crop=False,
                    detected_crop="none",
                    is_available=False,
                    is_user_selection_correct=False,
                    auto_selected=False,
                    action_status="REJECT_NOT_CROP",
                    final_selected_crop=None,
                    message_bn="ছবিটিতে কোনো ফসল বা গাছের পাতা সনাক্ত করা যায়নি। অনুগ্রহ করে আক্রান্ত ফসলের পাতার পরিষ্কার ছবি তুলে আবার আপলোড করুন।",
                )

        detected = predicted_crop or normalized_selected
        ai_out = RawAIVisionOutput(
            is_crop=True,
            is_clear_image=True,
            detected_crop=detected,
            detected_crop_bn=CROP_BN_NAMES.get(detected, detected),
        )

    # Step 3: Enforce strict gatekeeper decision logic
    if not ai_out.is_crop or not ai_out.is_clear_image or ai_out.detected_crop.lower() in ["none", "unknown", ""]:
        return VerificationResult(
            is_crop=False,
            detected_crop="none",
            is_available=False,
            is_user_selection_correct=False,
            auto_selected=False,
            action_status="REJECT_NOT_CROP",
            final_selected_crop=None,
            message_bn="এটি কোনো ফসলের ছবি নয় বা ছবিটি স্পষ্ট নয়। অনুগ্রহ করে ফসলের পাতার পরিষ্কার ছবি তুলে আবার আপলোড করুন।",
        )

    detected_crop = normalize_crop_name(ai_out.detected_crop)
    crop_bn = CROP_BN_NAMES.get(detected_crop, ai_out.detected_crop_bn or detected_crop)

    # Condition: Crop not in system's available crops list
    if detected_crop not in available_crops:
        return VerificationResult(
            is_crop=True,
            detected_crop=detected_crop,
            is_available=False,
            is_user_selection_correct=False,
            auto_selected=False,
            action_status="REJECT_NOT_AVAILABLE",
            final_selected_crop=None,
            message_bn=f"আপনি '{crop_bn}'-এর ছবি দিয়েছেন, কিন্তু এই ফসলটি বর্তমানে আমাদের সিস্টেমে নেই (Not Available)।",
        )

    # Condition: Matches user's selected crop
    if detected_crop == normalized_selected:
        return VerificationResult(
            is_crop=True,
            detected_crop=detected_crop,
            is_available=True,
            is_user_selection_correct=True,
            auto_selected=False,
            action_status="VALID_MATCH",
            final_selected_crop=detected_crop,
            message_bn="ফসলের ছবিটি সঠিক আছে।",
        )

    # Condition: Mismatch -> Auto-select
    return VerificationResult(
        is_crop=True,
        detected_crop=detected_crop,
        is_available=True,
        is_user_selection_correct=False,
        auto_selected=True,
        action_status="VALID_AUTO_SELECTED",
        final_selected_crop=detected_crop,
        message_bn=f"আপনি ভুল ফসল সিলেক্ট করেছিলেন। ছবি দেখে স্বয়ংক্রিয়ভাবে '{crop_bn}' সিলেক্ট করা হয়েছে।",
    )


if __name__ == "__main__":
    import numpy as np
    import pymupdf

    print("🌾 Testing Agricultural Image Verification Gatekeeper Service...")

    # Create dummy selfie image (skin tones: R=210, G=160, B=130)
    selfie_pix = pymupdf.Pixmap(pymupdf.csRGB, (0, 0, 150, 150), False)
    selfie_arr = np.frombuffer(selfie_pix.samples, dtype=np.uint8).reshape(150, 150, 3)
    selfie_arr[:, :] = [210, 160, 130]
    selfie_bytes = selfie_pix.tobytes("png")

    # Create dummy leaf image (green tones: R=45, G=150, B=40)
    leaf_pix = pymupdf.Pixmap(pymupdf.csRGB, (0, 0, 150, 150), False)
    leaf_arr = np.frombuffer(leaf_pix.samples, dtype=np.uint8).reshape(150, 150, 3)
    leaf_arr[:, :] = [45, 150, 40]
    leaf_bytes = leaf_pix.tobytes("png")

    async def run_tests():
        res_selfie = await verify_crop_image_gatekeeper(
            gemini_client=None,
            image_bytes=selfie_bytes,
            mime_type="image/png",
            selected_crop="potato",
        )
        print("\n--- Test 1: Uploading Selfie Photo ---")
        print(f"Action Status: {res_selfie.action_status}")
        print(f"Is Crop: {res_selfie.is_crop}")
        print(f"Message (Bangla): {res_selfie.message_bn}")
        assert res_selfie.is_crop is False, "Selfie should be REJECTED!"

        res_leaf = await verify_crop_image_gatekeeper(
            gemini_client=None,
            image_bytes=leaf_bytes,
            mime_type="image/png",
            selected_crop="potato",
        )
        print("\n--- Test 2: Uploading Green Leaf Photo ---")
        print(f"Action Status: {res_leaf.action_status}")
        print(f"Is Crop: {res_leaf.is_crop}")
        print(f"Message (Bangla): {res_leaf.message_bn}")
        assert res_leaf.is_crop is True, "Leaf should be ACCEPTED!"
        print("\n✅ All Gatekeeper tests passed successfully!")

    asyncio.run(run_tests())