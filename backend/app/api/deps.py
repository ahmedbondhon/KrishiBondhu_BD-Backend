# ============================================================================
# KrishiBondhu Bangladesh — Auth Dependencies
# FastAPI dependency injection for JWT authentication and RBAC
# ============================================================================

import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.security import decode_token_safe
from app.db.session import get_db
from app.models.auth import User
from app.repositories.auth import AuthRepository

# HTTP Bearer scheme (extracts token from Authorization header)
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Decode JWT, load user from DB, and return authenticated User.

    Raises 401 if token is missing/invalid or user not found.
    """
    if not credentials:
        raise AuthenticationError("Authorization header missing.")

    claims = decode_token_safe(credentials.credentials)
    if not claims or claims.get("type") != "access":
        raise AuthenticationError("Invalid or expired access token.")

    user_id_str = claims.get("sub")
    if not user_id_str:
        raise AuthenticationError("Token payload invalid.")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise AuthenticationError("Token payload invalid.")

    repo = AuthRepository(db)
    user = await repo.get_user_by_id(user_id)

    if not user:
        raise AuthenticationError("User not found.")

    if user.effective_status != "active":
        raise AuthenticationError("Account is not active.")

    return user


# Type alias for convenience
CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*allowed_roles: str):
    """Factory for role-based access control dependency.

    Handles 'admin' and 'administrator' as interchangeable aliases to prevent mismatch.
    """
    expanded = set(allowed_roles)
    if "administrator" in expanded:
        expanded.add("admin")
    if "admin" in expanded:
        expanded.add("administrator")
    if "technical_admin" in expanded:
        expanded.add("tech_admin")
    if "tech_admin" in expanded:
        expanded.add("technical_admin")

    async def role_checker(current_user: CurrentUser) -> User:
        if current_user.role_code not in expanded:
            raise PermissionDeniedError(
                f"This endpoint requires one of: {', '.join(allowed_roles)}."
            )
        return current_user

    return role_checker
