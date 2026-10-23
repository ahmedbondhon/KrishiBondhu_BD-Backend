# ============================================================================
# KrishiBondhu Bangladesh — Custom Exceptions
# Structured error handling for authentication, OTP, and user management
# ============================================================================

from fastapi import HTTPException, status


class AuthenticationError(HTTPException):
    """Raised when authentication credentials are invalid."""

    def __init__(self, detail: str = "Invalid credentials."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AccountLockedError(HTTPException):
    """Raised when an account is temporarily locked due to failed login attempts."""

    def __init__(self, lockout_minutes: int = 15):
        super().__init__(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked due to too many failed attempts. Try again after {lockout_minutes} minutes.",
        )


class AccountNotActiveError(HTTPException):
    """Raised when user account is not in active status."""

    def __init__(self, status_value: str = "inactive"):
        detail_map = {
            "inactive": "Account is deactivated. Please contact support.",
            "pending_approval": "Account is pending admin approval.",
            "suspended": "Account has been suspended. Please contact support.",
            "deleted": "Account not found.",
        }
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail_map.get(status_value, "Account is not active."),
        )


class DuplicateUserError(HTTPException):
    """Raised when a user with the same phone or email already exists."""

    def __init__(self, field: str = "phone_number"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A user with this {field} already exists.",
        )


class UserNotFoundError(HTTPException):
    """Raised when user is not found."""

    def __init__(self, identifier: str = "user"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No account found with this {identifier}.",
        )


class InvalidProfileDataError(HTTPException):
    """Raised when profile fields or geographic relationships are invalid."""

    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class RoleNotFoundError(HTTPException):
    """Raised when the requested role code doesn't exist."""

    def __init__(self, role_code: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: '{role_code}'.",
        )


class PermissionDeniedError(HTTPException):
    """Raised when a user lacks the required role/permission."""

    def __init__(self, detail: str = "You do not have permission to perform this action."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class InvalidRefreshTokenError(HTTPException):
    """Raised when a refresh token is invalid, expired, or already used."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )


class InvalidOtpError(HTTPException):
    """Raised when submitted OTP is incorrect or already used."""

    def __init__(self, detail: str = "Invalid OTP code. Please check and try again."):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class OtpExpiredError(HTTPException):
    """Raised when OTP has expired."""

    def __init__(self, detail: str = "OTP code has expired. Please request a new one."):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class PhoneNotVerifiedError(HTTPException):
    """Raised when registration is attempted without valid phone OTP verification."""

    def __init__(self, detail: str = "Phone number has not been verified via OTP. Please complete Step 1 first."):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class ConsentRequiredError(HTTPException):
    """Raised when mandatory Terms of Service & Privacy consent is not accepted."""

    def __init__(self, detail: str = "You must agree to the Terms of Service and Privacy Policy to register."):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


# Standard exception handler registration note:
# Exception handlers are unified in `app.main:app` using KrishiBondhu response envelope.

