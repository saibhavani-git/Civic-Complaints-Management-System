from fastapi import APIRouter, Depends

from app.core.rbac import get_current_user
from app.schemas.user import (
    ForgotPasswordRequest,
    ProfileUpdate,
    RefreshTokenRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.auth_service import (
    login_user,
    logout_user,
    refresh_access_token,
    register_user,
    request_password_reset,
    reset_password,
    update_profile,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserCreate):
    return await register_user(data)


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin):
    return await login_user(data)


@router.post("/refresh")
async def refresh(data: RefreshTokenRequest):
    return await refresh_access_token(data.refresh_token)


@router.post("/logout", status_code=204)
async def logout(data: RefreshTokenRequest):
    await logout_user(data.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        phone=current_user.phone,
        department_id=current_user.department_id,
        department_name=current_user.department_name,
        department_code=current_user.department_code,
        service_area=current_user.service_area,
        department_area=current_user.department_area,
    )


@router.patch("/me", response_model=UserResponse)
async def patch_me(data: ProfileUpdate, current_user=Depends(get_current_user)):
    return await update_profile(current_user.id, data)


@router.post("/forgot-password", status_code=204)
async def forgot_password(data: ForgotPasswordRequest):
    await request_password_reset(data.email)


@router.post("/reset-password", status_code=204)
async def post_reset_password(data: ResetPasswordRequest):
    await reset_password(data.token, data.new_password)
