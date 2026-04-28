from fastapi import APIRouter, Cookie, Depends, Response, status

from api.v1.models.auth_models import (
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    MessageResponse,
    RefreshResponse,
    RegisterRequest,
    ResetPasswordRequest,
    UserResponse,
)
from auth.dependencies import get_current_user
from services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
    return auth_service.register(body.email, body.password, body.full_name)


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, response: Response):
    return auth_service.login(body.email, body.password, response)


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(response: Response, refresh_token: str | None = Cookie(None)):
    return auth_service.refresh_tokens(refresh_token, response)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(None),
    _current_user: dict = Depends(get_current_user),
):
    auth_service.logout(refresh_token, response)
    return {"message": "Logged out successfully"}


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(body: ForgotPasswordRequest):
    return auth_service.forgot_password(body.email)


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(body: ResetPasswordRequest):
    return auth_service.reset_password(body.token, body.new_password)
