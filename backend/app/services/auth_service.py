import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from fastapi import HTTPException, status

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.config import get_settings
from app.db.database import get_database
from app.schemas.user import ProfileUpdate, UserCreate, UserLogin, UserResponse, TokenResponse
from app.utils.email import send_email


async def build_user_response(user: dict) -> UserResponse:
    db = get_database()
    dept_name = None
    dept_code = None
    dept_area = None
    dept_id = user.get("department_id")
    if dept_id:
        dept = await db.departments.find_one({"_id": dept_id if isinstance(dept_id, ObjectId) else ObjectId(dept_id)})
        if dept:
            dept_name = dept.get("name")
            dept_code = dept.get("code")
            dept_area = dept.get("coverage_area") or dept.get("description")

    return UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        full_name=user["full_name"],
        role=user["role"],
        phone=user.get("phone"),
        department_id=str(dept_id) if dept_id else None,
        department_name=dept_name,
        department_code=dept_code,
        service_area=user.get("service_area"),
        department_area=dept_area,
    )


async def create_staff_user(
    *,
    email: str,
    password: str,
    full_name: str,
    phone: str,
    role: str,
    department_id: str | None,
    service_area: str | None = None,
) -> UserResponse:
    db = get_database()
    normalized = email.lower()
    existing = await db.users.find_one({"email": normalized})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    area = (service_area or "").strip()
    if role == "officer" and len(area) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field area is required for field officers",
        )

    now = datetime.now(timezone.utc)
    doc = {
        "email": normalized,
        "password_hash": hash_password(password),
        "full_name": full_name,
        "phone": phone,
        "role": role,
        "department_id": ObjectId(department_id) if department_id else None,
        "service_area": area or None,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.users.insert_one(doc)
    doc["_id"] = result.inserted_id
    return await build_user_response(doc)


async def register_user(data: UserCreate) -> UserResponse:
    db = get_database()
    existing = await db.users.find_one({"email": data.email.lower()})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user_doc = {
        "email": data.email.lower(),
        "password_hash": hash_password(data.password),
        "full_name": data.full_name,
        "phone": data.phone,
        "role": "citizen",
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    result = await db.users.insert_one(user_doc)
    return UserResponse(
        id=str(result.inserted_id),
        email=user_doc["email"],
        full_name=user_doc["full_name"],
        role="citizen",
        phone=user_doc.get("phone"),
    )


async def login_user(data: UserLogin) -> TokenResponse:
    db = get_database()
    user = await db.users.find_one({"email": data.email.lower()})
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")

    user_id = str(user["_id"])
    access_token = create_access_token({"sub": user_id, "role": user["role"]})
    refresh_token = create_refresh_token({"sub": user_id})

    settings = get_settings()
    refresh_expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    await db.refresh_tokens.insert_one({
        "user_id": ObjectId(user_id),
        "token_hash": hashlib.sha256(refresh_token.encode()).hexdigest(),
        "expires_at": refresh_expire,
        "created_at": datetime.now(timezone.utc),
        "revoked": False,
    })

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=await build_user_response(user),
    )


async def refresh_access_token(refresh_token: str) -> dict:
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    db = get_database()
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    stored = await db.refresh_tokens.find_one({"token_hash": token_hash, "revoked": False})
    if not stored:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked or expired")

    user_id = payload["sub"]
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    access_token = create_access_token({"sub": user_id, "role": user["role"]})
    return {"access_token": access_token, "token_type": "bearer"}


async def logout_user(refresh_token: str) -> None:
    db = get_database()
    token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    await db.refresh_tokens.update_one({"token_hash": token_hash}, {"$set": {"revoked": True}})


async def request_password_reset(email: str) -> None:
    db = get_database()
    user = await db.users.find_one({"email": email.lower()})
    if not user:
        return

    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires = datetime.now(timezone.utc) + timedelta(hours=1)
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"password_reset_token": token_hash, "password_reset_expires": expires}},
    )

    settings = get_settings()
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    send_email(
        user["email"],
        "Humanizr password reset",
        f"Reset your password using this link (valid 1 hour):\n{reset_url}",
    )


async def reset_password(token: str, new_password: str) -> None:
    db = get_database()
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    user = await db.users.find_one(
        {
            "password_reset_token": token_hash,
            "password_reset_expires": {"$gt": datetime.now(timezone.utc)},
        }
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    await db.users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "password_hash": hash_password(new_password),
                "updated_at": datetime.now(timezone.utc),
            },
            "$unset": {"password_reset_token": "", "password_reset_expires": ""},
        },
    )


async def update_profile(user_id: str, data: ProfileUpdate) -> UserResponse:
    db = get_database()
    updates = {k: v for k, v in data.model_dump(exclude_none=True).items()}
    if not updates:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    else:
        updates["updated_at"] = datetime.now(timezone.utc)
        await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": updates})
        user = await db.users.find_one({"_id": ObjectId(user_id)})

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return await build_user_response(user)
