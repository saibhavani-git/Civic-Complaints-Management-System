from enum import Enum
from functools import wraps
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_token
from app.db.database import get_database
from app.schemas.user import UserInDB

security_scheme = HTTPBearer()


class Role(str, Enum):
    CITIZEN = "citizen"
    OFFICER = "officer"
    DEPT_ADMIN = "dept_admin"
    ADMIN = "admin"  # super admin


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> UserInDB:
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    db = get_database()
    user = await db.users.find_one({"_id": __import__("bson").ObjectId(user_id)})
    if not user or not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    from app.services.auth_service import build_user_response

    user["password_hash"] = user.get("password_hash", "")
    profile = await build_user_response(user)
    data = profile.model_dump()
    data["password_hash"] = user["password_hash"]
    data["is_active"] = user.get("is_active", True)
    data["created_at"] = user.get("created_at")
    return UserInDB(**data)


def require_roles(*roles: Role):
    async def role_checker(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
        if current_user.role not in [r.value for r in roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker
