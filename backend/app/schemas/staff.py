from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.validators import normalize_and_validate_phone


class AssignOfficerRequest(BaseModel):
    officer_id: str = Field(min_length=1)


def _validate_field_area(v: str | None) -> str:
    area = (v or "").strip()
    if len(area) < 2:
        raise ValueError("Field area is required (e.g. North zone, Wards 12–18)")
    if len(area) > 200:
        raise ValueError("Field area must be at most 200 characters")
    return area


class DeptWorkerCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2)
    phone: str = Field(min_length=10, max_length=20)
    service_area: str = Field(min_length=2, max_length=200)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return normalize_and_validate_phone(v)

    @field_validator("service_area")
    @classmethod
    def validate_service_area(cls, v: str) -> str:
        return _validate_field_area(v)
