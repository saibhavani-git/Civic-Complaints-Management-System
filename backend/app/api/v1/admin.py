from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.rbac import Role, get_current_user, require_roles
from app.db.database import get_database
from app.schemas.common import DepartmentCreate, DepartmentResponse
from app.schemas.user import AdminUserCreate, UserResponse
from app.services.auth_service import create_staff_user

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users")
async def list_users(_=Depends(require_roles(Role.ADMIN))):
    db = get_database()
    dept_by_id: dict[str, dict] = {}
    async for dept in db.departments.find({"is_active": True}, {"name": 1, "code": 1}):
        dept_by_id[str(dept["_id"])] = {"name": dept["name"], "code": dept["code"]}

    cursor = db.users.find({}, {"password_hash": 0}).sort([("role", 1), ("full_name", 1)])
    users = []
    async for doc in cursor:
        dept_id = str(doc["department_id"]) if doc.get("department_id") else None
        dept_meta = dept_by_id.get(dept_id) if dept_id else None
        users.append({
            "id": str(doc["_id"]),
            "email": doc["email"],
            "full_name": doc["full_name"],
            "role": doc["role"],
            "is_active": doc.get("is_active", True),
            "department_id": dept_id,
            "department_name": dept_meta["name"] if dept_meta else None,
            "department_code": dept_meta["code"] if dept_meta else None,
            "phone": doc.get("phone"),
        })
    return users


@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(data: AdminUserCreate, _=Depends(require_roles(Role.ADMIN))):
    return await create_staff_user(
        email=data.email,
        password=data.password,
        full_name=data.full_name,
        phone=data.phone,
        role=data.role.value,
        department_id=data.department_id,
        service_area=data.service_area,
    )


@router.get("/departments", response_model=list[DepartmentResponse])
async def list_departments(_=Depends(require_roles(Role.ADMIN))):
    db = get_database()
    cursor = db.departments.find({"is_active": True})
    depts = []
    async for doc in cursor:
        depts.append(DepartmentResponse(
            id=str(doc["_id"]),
            name=doc["name"],
            code=doc["code"],
            description=doc.get("description"),
            keywords=doc.get("keywords", []),
            is_active=doc.get("is_active", True),
            created_at=doc["created_at"],
        ))
    return depts


@router.post("/departments", response_model=DepartmentResponse, status_code=201)
async def create_department(data: DepartmentCreate, _=Depends(require_roles(Role.ADMIN))):
    db = get_database()
    doc = {
        "name": data.name,
        "code": data.code.upper(),
        "description": data.description,
        "keywords": data.keywords,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.departments.insert_one(doc)
    return DepartmentResponse(
        id=str(result.inserted_id),
        name=doc["name"],
        code=doc["code"],
        description=doc.get("description"),
        keywords=doc["keywords"],
        created_at=doc["created_at"],
    )
