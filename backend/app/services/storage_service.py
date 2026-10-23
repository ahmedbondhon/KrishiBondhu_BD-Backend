"""
services/storage_service.py
============================
Object storage abstraction layer for generating signed upload/download URLs.

Supported providers (configured via STORAGE_PROVIDER in .env):
  - 'supabase' : Supabase Storage (S3-compatible API)
  - 's3'       : AWS S3 or any S3-compatible storage

How the two-step signed upload works:
  1. generate_upload_url() : Creates a pre-signed PUT URL with a short expiry.
     The client uploads the file bytes directly to this URL using a PUT request.
     The backend never handles raw file bytes — better performance and security.

  2. generate_view_url()   : Creates a pre-signed GET URL so the client can
     access a private file without exposing permanent credentials.

Why not upload through the backend?
  - Avoids bandwidth cost on the backend server.
  - Faster for mobile clients (direct to CDN-edge storage).
  - Reduces server memory usage.
"""

import threading
import uuid
from datetime import datetime, timezone
from typing import Optional

try:
    import boto3
    from botocore.client import Config
except ImportError:
    boto3 = None
    Config = None

from app.core.config import settings


class StorageService:
    """
    Abstraction over object storage providers.
    Generates signed URLs for uploads and downloads.
    """

    def __init__(self):
        self._s3_client = None
        self._lock = threading.Lock()

    def warmup(self) -> None:

        """Pre-warm S3 client in a background thread to prevent blocking event loop on first request."""
        self._get_s3_client()

    def _get_s3_client(self):
        """
        Lazily initialize the S3-compatible client thread-safely.

        For Supabase: endpoint_url points to the Supabase S3 API.
        The access key ID is the project reference ID, while secret key is the service role key.
        For AWS S3: uses configured AWS credentials and region.
        """
        if self._s3_client is None:
            with self._lock:
                if self._s3_client is None:
                    if settings.storage_provider == "supabase":
                        project_ref = settings.supabase_project_ref
                        if not project_ref and settings.supabase_url:
                            clean_url = (
                                settings.supabase_url.replace("https://", "")
                                .replace("http://", "")
                                .rstrip("/")
                            )
                            host = clean_url.split("/")[0]
                            if ".supabase.co" in host:
                                project_ref = host.split(".supabase.co")[0]
                            elif "." in host:
                                project_ref = host.split(".")[0]
                        access_key = project_ref or settings.supabase_service_role_key
                        endpoint = f"{settings.supabase_url.rstrip('/')}/storage/v1/s3" if settings.supabase_url else ""
                        self._s3_client = boto3.client(
                            "s3",
                            endpoint_url=endpoint or None,
                            aws_access_key_id=access_key,
                            aws_secret_access_key=settings.supabase_service_role_key,
                            region_name="ap-southeast-1",
                            config=Config(signature_version="s3v4"),
                        )
                    else:
                        # Standard AWS S3
                        self._s3_client = boto3.client(
                            "s3",
                            aws_access_key_id=settings.aws_access_key_id,
                            aws_secret_access_key=settings.aws_secret_access_key,
                            region_name=settings.aws_region,
                            config=Config(signature_version="s3v4"),
                        )
        return self._s3_client

    def generate_upload_url(
        self,
        original_name: str,
        mime_type: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> tuple[str, str]:
        """
        Generate a pre-signed PUT URL for direct client upload.

        Returns:
            (upload_url, storage_path)
            - upload_url   : The pre-signed URL the client should PUT to.
            - storage_path : The object key (path) in the bucket, to be
                             passed back in the confirm-upload step.
        """
        # Build a user-scoped, collision-resistant storage path
        file_ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else "bin"
        folder = entity_type or "misc"
        file_uuid = uuid.uuid4()
        user_prefix = f"{user_id}/" if user_id else ""
        storage_path = f"{folder}/{user_prefix}{file_uuid}.{file_ext}"

        client = self._get_s3_client()
        upload_url = client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": settings.storage_bucket_name,
                "Key": storage_path,
                "ContentType": mime_type,
            },
            ExpiresIn=settings.storage_signed_url_expiry_seconds,
        )
        return upload_url, storage_path

    def generate_view_url(self, storage_path: str) -> str:
        """
        Generate a short-lived pre-signed GET URL for viewing a private file.

        The URL expires after `storage_signed_url_expiry_seconds` seconds.
        """
        client = self._get_s3_client()
        return client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": settings.storage_bucket_name,
                "Key": storage_path,
            },
            ExpiresIn=settings.storage_signed_url_expiry_seconds,
        )

    def check_file_exists(self, storage_path: str) -> bool:
        """
        Check if an object exists in storage via head_object.
        Returns True if the object exists, False otherwise.
        """
        try:
            client = self._get_s3_client()
            client.head_object(
                Bucket=settings.storage_bucket_name,
                Key=storage_path,
            )
            return True
        except Exception:
            return False



# Module-level singleton — one client per worker process
storage_service = StorageService()
