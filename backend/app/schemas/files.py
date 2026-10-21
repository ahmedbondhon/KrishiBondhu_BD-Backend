"""
schemas/files.py
================
Pydantic v2 schemas for the two-step signed image upload flow.

Two-step upload flow (explained):
  Step 1: Client calls POST /api/v1/files/upload-url
          → Backend validates file metadata and returns a signed upload URL.
          → Client uploads the file DIRECTLY to storage (Supabase/S3) using that URL.
          → Backend never receives the raw file bytes — this scales better.

  Step 2: Client calls POST /api/v1/files/confirm-upload
          → Client sends back the storage_path of the uploaded file.
          → Backend creates a system.files record (stores metadata, not the file).

  Step 3: To VIEW a private file, call GET /api/v1/files/{file_id}/view-url
          → Backend generates a short-lived signed download URL.
"""

from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ─────────────────────────────────────────────────────────
# Step 1 — Request Upload URL
# ─────────────────────────────────────────────────────────

class UploadUrlRequest(BaseModel):
    """
    POST /api/v1/files/upload-url

    Client sends file metadata BEFORE uploading.
    Backend validates constraints and returns a signed URL.

    Allowed MIME types: image/jpeg, image/png, image/webp
    Max file size: 5MB (5,242,880 bytes)
    """
    original_name: str = Field(..., max_length=255, description="Original filename from the device")
    mime_type: Literal["image/jpeg", "image/png", "image/webp"] = Field(..., description="MIME type of the image")
    file_size_bytes: int = Field(..., gt=0, le=5_242_880, description="File size in bytes (max 5MB)")
    entity_type: Optional[str] = Field(None, max_length=50, description="Entity this file belongs to (e.g., 'diagnosis_case')")
    entity_id: Optional[UUID] = None


class UploadUrlResponse(BaseModel):
    """Response from Step 1: contains the signed upload URL and storage path."""
    upload_url: str = Field(..., description="Pre-signed URL. PUT the file bytes directly to this URL.")
    storage_path: str = Field(..., description="Storage path to use in the confirm-upload step.")
    expires_in_seconds: int


# ─────────────────────────────────────────────────────────
# Step 2 — Confirm Upload
# ─────────────────────────────────────────────────────────

class ConfirmUploadRequest(BaseModel):
    """
    POST /api/v1/files/confirm-upload

    After the client has uploaded to storage, it confirms by sending
    the storage_path so the backend can register the file metadata.
    """
    storage_path: str = Field(..., description="Path returned from /upload-url step")
    original_name: str = Field(..., max_length=255)
    mime_type: str = Field(..., max_length=100)
    file_size_bytes: int = Field(..., gt=0)
    entity_type: Optional[str] = Field(None, max_length=50)
    entity_id: Optional[UUID] = None


class FileResponse(BaseModel):
    """Response containing the registered file metadata."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    storage_path: str
    original_name: str
    mime_type: str
    file_size_bytes: int
    provider: str
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None


# ─────────────────────────────────────────────────────────
# Step 3 — View URL (Signed Download)
# ─────────────────────────────────────────────────────────

class ViewUrlResponse(BaseModel):
    """Response from GET /api/v1/files/{file_id}/view-url"""
    view_url: str = Field(..., description="Short-lived signed URL to view/download the file")
    expires_in_seconds: int
