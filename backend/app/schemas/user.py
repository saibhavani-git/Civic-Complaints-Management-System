from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.schemas.validators import normalize_and_validate_phone


class UserRole(str, Enum):
    CITIZEN = "citizen"
    OFFICER = "officer"
    DEPT_ADMIN = "dept_admin"
    ADMIN = "admin"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2)
    phone: str = Field(min_length=10, max_length=20)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return normalize_and_validate_phone(v)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    id: str
    email: str
    full_name: str
    role: UserRole
    phone: Optional[str] = None
    department_id: Optional[str] = None
    department_name: Optional[str] = None
    department_code: Optional[str] = None
    service_area: Optional[str] = None  # officer beat / zone
    department_area: Optional[str] = None
    avatar_url: Optional[str] = None


class UserInDB(UserResponse):
    password_hash: str = Field(exclude=True)
    is_active: bool = True
    created_at: Optional[datetime] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class ProfileUpdate(BaseModel):
    full_name: str = Field(min_length=2)
    phone: str = Field(min_length=10, max_length=20)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return normalize_and_validate_phone(v)


class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    role: UserRole = UserRole.OFFICER
    phone: str = Field(min_length=10, max_length=20)
    department_id: Optional[str] = None
    service_area: Optional[str] = Field(default=None, max_length=200)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return normalize_and_validate_phone(v)

    @field_validator("service_area")
    @classmethod
    def validate_service_area(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not str(v).strip():
            return None
        area = str(v).strip()
        if len(area) < 2:
            raise ValueError("Field area must be at least 2 characters")
        return area

    @model_validator(mode="after")
    def staff_needs_department(self) -> "AdminUserCreate":
        if self.role in (UserRole.OFFICER, UserRole.DEPT_ADMIN) and not self.department_id:
            raise ValueError("department_id is required for officer and department admin")
        if self.role == UserRole.OFFICER:
            if not (self.service_area or "").strip():
                raise ValueError("Field area is required for field officers")
        if self.role == UserRole.CITIZEN:
            raise ValueError("Citizens must register via /auth/register")
        return self
