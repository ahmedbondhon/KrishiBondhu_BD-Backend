# ============================================================================
# KrishiBondhu Bangladesh — Supabase Data Client
# Direct REST client for Supabase PostgreSQL (PostgREST API)
# ============================================================================

import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from app.core.config import get_settings
from app.core.security import normalize_bd_phone

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Async REST client interacting with Supabase PostgREST API."""

    def __init__(self):
        settings = get_settings()
        sb_url = settings.supabase_url.rstrip('/') if settings.supabase_url else "http://localhost:8000"
        self.base_url = f"{sb_url}/rest/v1"
        self.headers = {
            "apikey": settings.supabase_service_role_key,
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        self._client: httpx.AsyncClient | None = None

    def get_client(self) -> httpx.AsyncClient:
        """Reuse a single shared httpx.AsyncClient to eliminate TCP/TLS overhead."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client

    async def close(self) -> None:
        """Close shared connection pool on app shutdown."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Centralized HTTP request handler to eliminate try/except boilerplate."""
        try:
            client = self.get_client()
            m = method.lower()
            url = f"{self.base_url}/{endpoint}"
            headers = kwargs.pop("headers", self.headers)
            if hasattr(client, m):
                fn = getattr(client, m)
                resp = await fn(url, headers=headers, **kwargs)
            else:
                resp = await client.request(method, url, headers=headers, **kwargs)
            if resp.status_code in (200, 201):
                return resp.json()
            if resp.status_code == 204:
                return True
            logger.warning(f"Supabase {method} /{endpoint} failed: {resp.status_code} - {resp.text}")
        except Exception as e:
            logger.error(f"Supabase error on {method} /{endpoint}: {e}")
        return None

    async def _get_user(self, filter_query: str) -> dict[str, Any] | None:
        data = await self._request("GET", f"users?{filter_query}&select=*,roles(code,name)&is_deleted=eq.false")
        if data:
            user = data[0]
            role = user.get("roles") if isinstance(user.get("roles"), dict) else {}
            user["role_code"] = role.get("code", "farmer")
            user["role_name"] = role.get("name", "Farmer")
            return user
        return None

    async def get_user_by_phone(self, phone: str) -> dict[str, Any] | None:
        return await self._get_user(f"phone_number=eq.{normalize_bd_phone(phone)}")

    async def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        return await self._get_user(f"email=eq.{email}")

    async def get_role_id_by_code(self, code: str) -> str | None:
        data = await self._request("GET", f"roles?code=eq.{code}")
        return data[0]["id"] if data else None

    async def create_user(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        if payload.get("phone_number"):
            payload["phone_number"] = normalize_bd_phone(payload["phone_number"])
        data = await self._request("POST", "users", json=payload)
        if not data and "preferred_communication" in payload:
            fallback = {k: v for k, v in payload.items() if k != "preferred_communication"}
            data = await self._request("POST", "users", json=fallback)
        return data[0] if isinstance(data, list) and data else data

    async def update_last_login(self, user_id: str) -> bool:
        now_iso = datetime.now(timezone.utc).isoformat()
        return bool(await self._request("PATCH", f"users?id=eq.{user_id}", json={"last_login_at": now_iso}))

    async def record_login_attempt(self, user_id: str, ip: str | None, user_agent: str | None, success: bool) -> None:
        await self._request("POST", "login_attempts", json={
            "user_id": user_id, "ip_address": ip, "user_agent": user_agent, "success": success
        })

    async def update_user_profile(self, user_id: str, payload: dict[str, Any]) -> bool:
        """Update farmer profile details in Supabase auth.users table."""
        # Convert any UUID objects to strings
        cleaned = {}
        for k, v in payload.items():
            if v is not None:
                cleaned[k] = str(v)
            else:
                cleaned[k] = None
        cleaned["updated_at"] = datetime.now(timezone.utc).isoformat()
        return bool(await self._request("PATCH", f"users?id=eq.{user_id}", json=cleaned))

    async def update_user_password(self, phone: str, password_hash: str) -> bool:
        phone = normalize_bd_phone(phone)
        return bool(await self._request("PATCH", f"users?phone_number=eq.{phone}", json={"password_hash": password_hash}))

    async def update_user_status(self, user_id: str, status: str) -> bool:
        return bool(await self._request("PATCH", f"users?id=eq.{user_id}", json={"status": status, "is_active": status == "active"}))

    async def update_user_email_verified(self, user_id: str, verified: bool = True) -> bool:
        return bool(await self._request("PATCH", f"users?id=eq.{user_id}", json={"email_verified": verified}))

    async def record_otp(self, phone: str, otp_hash: str, expires_at: datetime) -> bool:
        return bool(await self._request("POST", "otp_logs", json={
            "phone_number": normalize_bd_phone(phone),
            "otp_hash": otp_hash,
            "expires_at": expires_at.isoformat(),
            "is_verified": False,
        }))

    async def mark_otp_verified(self, phone: str, otp_hash: str) -> bool:
        phone = normalize_bd_phone(phone)
        return bool(await self._request("PATCH", f"otp_logs?phone_number=eq.{phone}&otp_hash=eq.{otp_hash}", json={"is_verified": True}))

    async def record_user_consent(self, user_id: str, code: str, ip: str | None, ua: str | None, is_granted: bool = True) -> None:
        ct = await self._request("GET", f"consent_types?code=eq.{code}")
        if ct:
            now_iso = datetime.now(timezone.utc).isoformat()
            await self._request("POST", "user_consents", json={
                "user_id": user_id, "consent_type_id": ct[0]["id"],
                "is_granted": is_granted, "ip_address": ip, "user_agent": ua,
                "granted_at": now_iso if is_granted else None,
                "created_at": now_iso,
            })

    async def upload_storage_file(self, bucket: str, path: str, content: bytes, mime_type: str) -> str | None:
        """Upload a file to Supabase Storage bucket and return its public URL."""
        settings = get_settings()
        url = f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{bucket}/{path.lstrip('/')}"
        headers = {
            "apikey": settings.supabase_service_role_key,
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
            "Content-Type": mime_type,
            "x-upsert": "true",
        }
        try:
            client = self.get_client()
            resp = await client.post(url, headers=headers, content=content)
            if resp.status_code in (200, 201):
                return f"{settings.supabase_url.rstrip('/')}/storage/v1/object/public/{bucket}/{path.lstrip('/')}"
            logger.error(f"Supabase storage upload failed: {resp.status_code} - {resp.text}")
        except Exception as e:
            logger.error(f"Supabase storage upload error: {e}")
        return None

    async def delete_storage_file(self, bucket: str, path: str) -> bool:
        """Delete a file from Supabase Storage bucket."""
        settings = get_settings()
        url = f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{bucket}"
        headers = {
            "apikey": settings.supabase_service_role_key,
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
            "Content-Type": "application/json",
        }
        try:
            client = self.get_client()
            resp = await client.request("DELETE", url, headers=headers, json={"prefixes": [path.lstrip("/")]})
            return resp.status_code in (200, 204)
        except Exception as e:
            logger.error(f"Supabase storage delete error: {e}")
        return False


supabase_client = SupabaseClient()