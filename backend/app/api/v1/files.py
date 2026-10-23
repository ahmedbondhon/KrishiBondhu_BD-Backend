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

router = APIRouter(prefix="/files", tags=["File Storage"])

# Allowed MIME types for crop disease images
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


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
      - MIME type must be image/jpeg, image/png, or image/webp.
      - File size must not exceed 5 MB (5,242,880 bytes).
    """
    if payload.mime_type not in ALLOWED_MIME_TYPES:
        return error_response(
            message="Unsupported file type",
            error_code="INVALID_MIME_TYPE",
            status_code=422,
            details=[{"field": "mime_type", "message_bn": "শুধুমাত্র JPEG, PNG বা WebP ছবি অনুমোদিত।"}],
        )

    if payload.file_size_bytes > MAX_FILE_SIZE_BYTES:
        return error_response(
            message="File too large",
            error_code="FILE_TOO_LARGE",
            status_code=422,
            details=[{"field": "file_size_bytes", "message_bn": "ছবির আকার সর্বোচ্চ ৫ MB হতে পারবে।"}],
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
    if user_id_str not in payload.storage_path:
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

    system_file = SystemFile(
        uploaded_by=current_user.id,
        original_name=payload.original_name,
        storage_path=payload.storage_path,
        bucket_name=settings.storage_bucket_name,
        provider=settings.storage_provider,
        mime_type=payload.mime_type,
        file_size_bytes=payload.file_size_bytes,
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

    # Access control: only uploader or admin
    if file.uploaded_by != current_user.id and current_user.role.code not in ("admin", "tech_admin"):
        return error_response("Access denied", "FORBIDDEN", 403)

    view_url = storage_service.generate_view_url(file.storage_path)

    return success_response(
        data=ViewUrlResponse(
            view_url=view_url,
            expires_in_seconds=settings.storage_signed_url_expiry_seconds,
        ).model_dump(),
        message="ভিউ URL প্রস্তুত।",
    )
