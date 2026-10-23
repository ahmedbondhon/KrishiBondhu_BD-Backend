"""
core/dependencies.py
====================
FastAPI dependency injection functions used across all route handlers.

Key dependencies:
  - get_db()            : Yields an async SQLAlchemy database session per request.
  - get_current_user()  : Extracts and validates the JWT Bearer token, returns the active user.
  - require_roles()     : Factory that returns a dependency enforcing one or more allowed roles (RBAC).

How to use in route handlers:
    @router.get("/protected")
    async def my_endpoint(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        ...

    # Restrict to experts and admins only:
    @router.post("/expert-only", dependencies=[Depends(require_roles("expert", "admin"))])
    async def expert_endpoint(...):
        ...
"""

from typing import Sequence
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import verify_access_token
from app.db.session import async_session_factory, get_db
from app.models.auth import User



# ─────────────────────────────────────────────────────────
# Authentication
# ─────────────────────────────────────────────────────────

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validate the Bearer JWT token from the Authorization header.

    Steps:
      1. Extract the token string from the Authorization header.
      2. Decode and verify the JWT (checks signature + expiry).
      3. Load the matching user from the database.
      4. Confirm the user account is active and not soft-deleted.

    Raises 401 if any step fails.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "UNAUTHORIZED", "message_bn": "আপনার লগইন মেয়াদ শেষ হয়ে গেছে। পুনরায় লগইন করুন।"},
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise credentials_exception

    payload = verify_access_token(credentials.credentials)
    if not payload:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if not user_id:
        raise credentials_exception

    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()

    if user is None or not user.is_active or user.is_deleted:
        raise credentials_exception

    return user


# ─────────────────────────────────────────────────────────
# Role-Based Access Control (RBAC)
# ─────────────────────────────────────────────────────────

def require_roles(*allowed_role_codes: str):
    """
    Dependency factory for role-based access control.

    Returns a FastAPI dependency function that raises 403 Forbidden if the
    authenticated user's role is not in the allowed set.
    """
    expanded = set(allowed_role_codes)
    if "administrator" in expanded:
        expanded.add("admin")
    if "admin" in expanded:
        expanded.add("administrator")
    if "technical_admin" in expanded:
        expanded.add("tech_admin")
    if "tech_admin" in expanded:
        expanded.add("technical_admin")

    async def _check_role(current_user: User = Depends(get_current_user)) -> User:
        user_role = current_user.role_code if hasattr(current_user, "role_code") else (current_user.role.code if current_user.role else "farmer")
        if user_role not in expanded:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "message_bn": "আপনার এই পৃষ্ঠায় প্রবেশের অনুমতি নেই।",
                },
            )
        return current_user

    return _check_role
