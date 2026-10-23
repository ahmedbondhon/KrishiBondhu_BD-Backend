"""
api/v1/files.py
===============
HTTP route handlers for the two-step secure image upload flow.

Routes:
  POST /api/v1/files/upload-url        → Step 1: Get signed upload URL
  POST /api/v1/files/confirm-upload    → Step 2: Confirm file was uploaded
  GET  /api/v1/files/{file_id}/view-url → Step 3: Get signed view URL

All routes require authentication.

Flow diagram:
  Client            Backend          Storage (Supabase/S3)
    │                  │                      │
    │─POST upload-url→ │                      │
    │←signed PUT URL── │                      │
    │                  │                      │
    │──PUT file bytes──────────────────────→  │ (direct upload, backend bypassed)
    │←200 OK────────────────────────────────  │
    │                  │                      │
    │─POST confirm ──→ │                      │
    │←file metadata──  │ (stores in DB)       │
    │                  │                      │
    │─GET view-url───→ │                      │
    │←signed GET URL── │                      │
    │──GET file──────────────────────────── → │
    │←file bytes─────────────────────────── - │
"""

from typing import Optional
from pydantic import BaseModel
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.responses import error_response, success_response
from app.models.auth import User
from app.models.system import SystemFile
from app.schemas.files import (
    ConfirmUploadRequest,
    FileResponse,
    UploadUrlRequest,
    UploadUrlResponse,
    ViewUrlResponse,
)
from app.services.storage_service import storage_service
from app.core.config import settings

# 5 MB maximum allowed file size
MAX_FILE_SIZE_BYTES: int = getattr(settings, "max_file_size_bytes", 5 * 1024 * 1024)

class VerifyCropImageRequest(BaseModel):
    image_base64: Optional[str] = None
    storage_path: Optional[str] = None
    selected_crop: str = "potato"
    mime_type: str = "image/jpeg"
    strict_crop_match: bool = False

router = APIRouter(prefix="/files", tags=["File Storage"])

# Allowed MIME types for crop disease images and expert/farmer audio voice notes
ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_AUDIO_MIME_TYPES = {
    "audio/mpeg",
    "audio/mp4",
    "audio/wav",
    "audio/webm",
    "audio/ogg",
    "audio/m4a",
    "audio/x-m4a",
    "audio/aac",
}
ALLOWED_MIME_TYPES = ALLOWED_IMAGE_MIME_TYPES | ALLOWED_AUDIO_MIME_TYPES


@router.post("/upload-url", summary="Request a signed upload URL (Step 1 of 2)")
async def get_upload_url(
    payload: UploadUrlRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Validate file metadata and return a pre-signed PUT URL.

    The client must:
      1. Send a PUT request with the file bytes to `upload_url`.
      2. Then call /files/confirm-upload with the `storage_path`.

    Validations:
      - MIME type must be an allowed image or audio format.
      - File size must not exceed configured limit.
    """
    if payload.mime_type not in ALLOWED_MIME_TYPES:
        return error_response(
            message="Unsupported file type",
            error_code="INVALID_MIME_TYPE",
            status_code=422,
            details=[{"field": "mime_type", "message_bn": "শুধুমাত্র অনুমোদিত ছবি (JPEG, PNG, WebP) বা অডিও ফাইল অনুমোদিত।"}],
        )

    max_size = getattr(settings, "max_file_size_bytes", 5 * 1024 * 1024)
    if payload.file_size_bytes > max_size:
        return error_response(
            message="File too large",
            error_code="FILE_TOO_LARGE",
            status_code=422,
            details=[{"field": "file_size_bytes", "message_bn": f"ফাইলের আকার সর্বোচ্চ {max_size // (1024 * 1024)} MB হতে পারবে।"}],
        )

    upload_url, storage_path = storage_service.generate_upload_url(
        original_name=payload.original_name,
        mime_type=payload.mime_type,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        user_id=current_user.id,
    )

    return success_response(
        data=UploadUrlResponse(
            upload_url=upload_url,
            storage_path=storage_path,
            expires_in_seconds=settings.storage_signed_url_expiry_seconds,
        ).model_dump(),
        message="আপলোড URL প্রস্তুত।",
    )


@router.post("/confirm-upload", status_code=201, summary="Confirm file upload and register metadata (Step 2 of 2)")
async def confirm_upload(
    payload: ConfirmUploadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    After the client has uploaded the file to storage, call this endpoint
    to register the file metadata in the database (system.files table).

    Returns the file record with its UUID, which is used to:
      - Attach images to a diagnosis case.
      - Set a user avatar.
    """
    # Storage path validation: ensure path was issued to this user
    user_id_str = str(current_user.id)
    # Reject directory traversal attempts and ensure strict user segment prefix
    norm_path = payload.storage_path.replace("\\", "/").strip("/")
    path_segments = norm_path.split("/")
    if ".." in path_segments or "." in path_segments or len(path_segments) < 2 or path_segments[1] != user_id_str:
        return error_response(
            message="Invalid storage path for current user",
            error_code="FORBIDDEN_STORAGE_PATH",
            status_code=403,
            details=[{"field": "storage_path", "message_bn": "অন্য ব্যবহারকারীর স্টোরেজ পাথ ব্যবহার করা অনুমোদিত নয়।"}],
        )

    # Check for duplicate registration of the same storage path
    existing_file = await db.execute(
        select(SystemFile).where(SystemFile.storage_path == payload.storage_path)
    )
    if existing_file.scalar_one_or_none():
        return error_response(
            message="File already registered",
            error_code="FILE_ALREADY_REGISTERED",
            status_code=409,
            details=[{"field": "storage_path", "message_bn": "এই ফাইলটি ইতিমধ্যে নিবন্ধিত আছে।"}],
        )

    # Verify file actually exists in storage before saving to DB
    meta = await storage_service.get_file_metadata(payload.storage_path)
    if not meta:
        return error_response(
            message="Uploaded file not found in storage",
            error_code="FILE_NOT_FOUND_IN_STORAGE",
            status_code=400,
            details=[{"field": "storage_path", "message_bn": "ক্লাউড স্টোরেজে ফাইলটি পাওয়া যায়নি। অনুগ্রহ করে প্রথমে ফাইল আপলোড করুন।"}],
        )

    # Validate actual file size stored in bucket against maximum limit
    actual_size = meta.get("content_length", 0)
    if actual_size > MAX_FILE_SIZE_BYTES:
        # Delete oversized file from bucket immediately
        await storage_service.delete_file(payload.storage_path)
        return error_response(
            message="Uploaded file size exceeds maximum permitted limit",
            error_code="FILE_TOO_LARGE",
            status_code=422,
            details=[{"field": "file_size_bytes", "message_bn": "স্টোরেজে আপলোডকৃত ফাইলের আকার সর্বোচ্চ ৫ MB সীমার বেশি।"}],
        )
    # Strict Agricultural Gatekeeper Image Verification
    # If the file is for a crop diagnosis case or crop catalog, verify it is a valid crop
    is_crop_entity = payload.entity_type in ("diagnosis_case", "crops", "crop_image", "case_image", "crop")
    if is_crop_entity and payload.mime_type.startswith("image/"):
        file_bytes = await storage_service.get_file_bytes(payload.storage_path)
        if file_bytes:
            from app.services.image_gatekeeper import (
                verify_crop_image_gatekeeper,
                get_system_available_crops,
                get_gemini_client,
            )
            avail_crops = await get_system_available_crops(db)
            verification = await verify_crop_image_gatekeeper(
                gemini_client=get_gemini_client(),
                image_bytes=file_bytes,
                mime_type=payload.mime_type,
                selected_crop="potato",
                available_crops=avail_crops,
            )
            if not verification.is_crop or verification.action_status == "REJECT_NOT_CROP":
                await storage_service.delete_file(payload.storage_path)
                return error_response(
                    message="Image rejected: Not a valid crop image",
                    error_code="REJECT_NOT_CROP",
                    status_code=422,
                    details=[{"field": "file", "message_bn": verification.message_bn}],
                )

    system_file = SystemFile(
        uploaded_by=current_user.id,
        original_name=payload.original_name,
        storage_path=payload.storage_path,
        bucket_name=settings.storage_bucket_name,
        provider=settings.storage_provider,
        mime_type=payload.mime_type,
        file_size_bytes=actual_size if actual_size > 0 else payload.file_size_bytes,
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        is_processed=False,
    )
    db.add(system_file)
    await db.flush()

    return success_response(
        data=FileResponse.model_validate(system_file).model_dump(),
        message="ফাইল সফলভাবে নিবন্ধিত হয়েছে।",
        status_code=201,
    )


@router.get("/{file_id}/view-url", summary="Get a signed URL to view a private file (Step 3)")
async def get_view_url(
    file_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a short-lived signed URL to view/download a private stored file.

    The signed URL expires after `storage_signed_url_expiry_seconds` seconds.
    Only the user who uploaded the file (or admins) can access it.
    """
    result = await db.execute(
        select(SystemFile).where(
            SystemFile.id == file_id,
            SystemFile.is_deleted == False,
        )
    )
    file = result.scalar_one_or_none()
    if not file:
        return error_response("File not found", "FILE_NOT_FOUND", 404)

    # Access control: uploader or admin/tech_admin; experts/agents may only access diagnosis case files
    user_role = getattr(current_user, "role_code", "") or (current_user.role.code if getattr(current_user, "role", None) else "")
    allowed_roles = ("admin", "administrator", "tech_admin", "technical_admin", "expert", "agent")
    if file.uploaded_by != current_user.id and user_role not in allowed_roles:
        return error_response("Access denied", "FORBIDDEN", 403)

    if file.uploaded_by != current_user.id and user_role not in ("admin", "administrator", "tech_admin", "technical_admin"):
        # Experts and agents are only authorized to view case-related media
        allowed_entities = ("diagnosis_case", "case_image", "voice_note", "audio_advisory", None)
        if file.entity_type not in allowed_entities:
            return error_response("Access denied: Private non-case file", "FORBIDDEN", 403)

    view_url = storage_service.generate_view_url(file.storage_path)

    return success_response(
        data=ViewUrlResponse(
            view_url=view_url,
            expires_in_seconds=settings.storage_signed_url_expiry_seconds,
        ).model_dump(),
        message="ভিউ URL প্রস্তুত।",
    )


@router.post("/verify-crop-image", summary="Verify whether image is a valid crop using Gatekeeper")
async def verify_crop_image(
    payload: VerifyCropImageRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Agricultural Gatekeeper inspection endpoint.
    Inspects image bytes (base64 or storage_path) to ensure it is not a selfie,
    document, animal, or non-plant, and validates matching crop catalog.
    """
    import base64
    from app.services.image_gatekeeper import (
        verify_crop_image_gatekeeper,
        get_system_available_crops,
        get_gemini_client,
    )

    img_bytes: Optional[bytes] = None
    mime = payload.mime_type or "image/jpeg"

    if payload.image_base64:
        raw_b64 = payload.image_base64
        if "data:" in raw_b64 and ";base64," in raw_b64:
            header, raw_b64 = raw_b64.split(";base64,", 1)
            if "data:" in header:
                mime = header.replace("data:", "").strip()
        try:
            img_bytes = base64.b64decode(raw_b64)
        except Exception:
            return error_response(
                message="Invalid base64 image data",
                error_code="INVALID_BASE64",
                status_code=400,
                details=[{"field": "image_base64", "message_bn": "ইমেজের ডাটা সঠিক নয়।"}],
            )
    elif payload.storage_path:
        img_bytes = await storage_service.get_file_bytes(payload.storage_path)
        if not img_bytes:
            return error_response(
                message="File not found in storage",
                error_code="FILE_NOT_FOUND",
                status_code=404,
                details=[{"field": "storage_path", "message_bn": "স্টোরেজে ফাইলটি পাওয়া যায়নি।"}],
            )

    if not img_bytes:
        return error_response(
            message="No image provided",
            error_code="NO_IMAGE",
            status_code=400,
            details=[{"field": "image_base64", "message_bn": "কোনো ছবি প্রদান করা হয়নি।"}],
        )

    avail_crops = await get_system_available_crops(db)
    verification = await verify_crop_image_gatekeeper(
        gemini_client=get_gemini_client(),
        image_bytes=img_bytes,
        mime_type=mime,
        selected_crop=payload.selected_crop,
        available_crops=avail_crops,
    )

    if getattr(payload, "strict_crop_match", True) and not verification.is_user_selection_correct and verification.is_crop:
        verification.action_status = "REJECT_CROP_MISMATCH"
        verification.auto_selected = False

    if not verification.is_crop or verification.action_status in (
        "REJECT_NOT_CROP",
        "REJECT_CROP_MISMATCH",
        "REJECT_NOT_AVAILABLE",
    ):
        return error_response(
            message=verification.message_bn,
            error_code=verification.action_status,
            status_code=422,
            details=[
                {
                    "field": "crop",
                    "action_status": verification.action_status,
                    "detected_crop": verification.detected_crop,
                    "selected_crop": payload.selected_crop,
                    "message_bn": verification.message_bn,
                }
            ],
        )

    return success_response(
        data=verification.model_dump(),
        message=verification.message_bn,
    )
