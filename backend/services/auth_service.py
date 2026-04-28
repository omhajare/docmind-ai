import uuid
import secrets

from fastapi import HTTPException, Response, status

from config import get_settings
from auth.jwt_handler import create_access_token
from auth.password_handler import hash_password, verify_password
from repositories import user_repository, token_repository
from mailer.email_sender import send_password_reset_email
from utils.logger import logger

settings = get_settings()

COOKIE_NAME = "refresh_token"


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    """Set the refresh token as an httpOnly cookie with environment-aware attributes."""
    if settings.is_production:
        response.set_cookie(
            key=COOKIE_NAME,
            value=raw_token,
            httponly=True,
            secure=True,
            samesite="none",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            path="/",
        )
    else:
        response.set_cookie(
            key=COOKIE_NAME,
            value=raw_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            path="/",
        )


def _clear_refresh_cookie(response: Response) -> None:
    """Clear the refresh token cookie."""
    if settings.is_production:
        response.delete_cookie(key=COOKIE_NAME, path="/", samesite="none", secure=True)
    else:
        response.delete_cookie(key=COOKIE_NAME, path="/", samesite="lax", secure=False)


def register(email: str, password: str, full_name: str) -> dict:
    """Register a new user."""
    email = email.strip().lower()
    full_name = full_name.strip()

    existing = user_repository.find_by_email(email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    pw_hash = hash_password(password)
    user = user_repository.create(email, pw_hash, full_name)
    logger.info(f"User registered: {user['id']}")
    return {"id": str(user["id"]), "email": user["email"], "full_name": user["full_name"]}


def login(email: str, password: str, response: Response) -> dict:
    """Authenticate user, return access token, set refresh cookie."""
    email = email.strip().lower()

    user = user_repository.find_by_email(email)
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Generate tokens
    access_token = create_access_token(str(user["id"]), user["email"])
    raw_refresh = str(uuid.uuid4())
    token_repository.create_refresh_token(
        str(user["id"]), raw_refresh, settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    # Set cookie
    _set_refresh_cookie(response, raw_refresh)

    # Update last_login
    user_repository.update_last_login(str(user["id"]))

    logger.info(f"User logged in: {user['id']}")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user["id"]),
            "email": user["email"],
            "full_name": user["full_name"],
        },
    }


def refresh_tokens(raw_refresh: str | None, response: Response) -> dict:
    """Validate refresh token, rotate it, return new access token."""
    if not raw_refresh:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )

    token_record = token_repository.find_refresh_token(raw_refresh)
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = user_repository.find_by_id(str(token_record["user_id"]))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    # Rotate: revoke old, create new
    token_repository.revoke_refresh_token(raw_refresh)
    new_raw_refresh = str(uuid.uuid4())
    token_repository.create_refresh_token(
        str(user["id"]), new_raw_refresh, settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    _set_refresh_cookie(response, new_raw_refresh)

    access_token = create_access_token(str(user["id"]), user["email"])
    return {"access_token": access_token, "token_type": "bearer"}


def logout(raw_refresh: str | None, response: Response) -> None:
    """Revoke refresh token and clear cookie."""
    if raw_refresh:
        token_repository.revoke_refresh_token(raw_refresh)
    _clear_refresh_cookie(response)


def forgot_password(email: str) -> dict:
    """Generate a password reset token and send email."""
    email = email.strip().lower()
    user = user_repository.find_by_email(email)

    # Always return success to prevent email enumeration
    message = "If this email is registered, you will receive a reset link."

    if user:
        raw_token = secrets.token_urlsafe(32)
        token_repository.create_reset_token(
            str(user["id"]), raw_token, settings.PASSWORD_RESET_EXPIRE_MINUTES
        )
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={raw_token}"
        try:
            send_password_reset_email(user["email"], user["full_name"], reset_link)
        except Exception as e:
            logger.error(f"Failed to send reset email: {e}")
            # In local mode, log the link so the developer can use it
            if not settings.is_production:
                logger.info(f"Password reset link (local): {reset_link}")

    return {"message": message}


def reset_password(raw_token: str, new_password: str) -> dict:
    """Validate reset token and update password."""
    token_record = token_repository.find_reset_token(raw_token)
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    new_hash = hash_password(new_password)
    user_repository.update_password(str(token_record["user_id"]), new_hash)
    token_repository.mark_reset_token_used(str(token_record["id"]))

    # Revoke all refresh tokens for security
    token_repository.revoke_all_user_tokens(str(token_record["user_id"]))

    logger.info(f"Password reset for user: {token_record['user_id']}")
    return {"message": "Password has been reset successfully"}
