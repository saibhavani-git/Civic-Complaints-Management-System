import logging
import re
from datetime import datetime, timezone

import cloudinary
import cloudinary.uploader
from bson import ObjectId
from fastapi import HTTPException, UploadFile, status

from app.integrations.ai_client import run_ai_pipeline
from app.services.blockchain_service import append_audit_block
from app.services.cluster_service import refresh_clusters_for_location
from app.config import get_settings
from app.db.database import get_database
from app.schemas.complaint import ComplaintCreate, ComplaintResponse, ComplaintStatus, Priority
from app.services.notification_service import create_notification

logger = logging.getLogger(__name__)


def _normalize_role(role: str | object) -> str:
    if role is None:
        return "citizen"
    if hasattr(role, "value"):
        return str(role.value).lower().strip()
    return str(role).lower().strip()


async def _cursor_to_list(cursor, *, length: int) -> list[dict]:
    """Motor cursors must use to_list — async list comps break on some runtimes."""
    if isinstance(cursor, list):
        return cursor
    if hasattr(cursor, "to_list"):
        return await cursor.to_list(length=length)
    out: list[dict] = []
    async for doc in cursor:
        out.append(doc)
    return out

_OFFICER_ACTIVE_STATUSES = [
    ComplaintStatus.ASSIGNED.value,
    ComplaintStatus.WORK_STARTED.value,
    ComplaintStatus.IN_PROGRESS.value,
]

_VALID_STATUSES = {s.value for s in ComplaintStatus}
_VALID_PRIORITIES = {p.value for p in Priority}


def _coerce_status(value: str | None) -> str:
    if value and value in _VALID_STATUSES:
        return value
    return ComplaintStatus.PENDING.value


def _coerce_priority(value: str | None) -> str:
    if value and value in _VALID_PRIORITIES:
        return value
    return "medium"


def _sanitize_images(images: list | None) -> list[dict]:
    now = datetime.now(timezone.utc)
    out: list[dict] = []
    for img in images or []:
        if not isinstance(img, dict) or not img.get("url"):
            continue
        out.append(
            {
                "url": img["url"],
                "public_id": img.get("public_id") or "",
                "uploaded_at": img.get("uploaded_at") or now,
            }
        )
    return out


_INTERNAL_NOTE_MARKERS = (
    "bullmq",
    "gemini",
    "openai",
    "ai routing",
    "ai pipeline",
    "ai queue",
    "ai processing failed",
    "returned to queue",
    "model_",
    "routing_source",
    "redis",
    "worker entrypoint",
)


def _public_timeline_note(note: str | None) -> str | None:
    """Strip queue/AI implementation details from timeline notes (all viewers)."""
    if not note or not str(note).strip():
        return None
    text = str(note).strip()
    lower = text.lower()

    if "bullmq" in lower or "picked up from" in lower:
        return "Review started"
    if "waiting in ai queue" in lower or lower.startswith("complaint submitted — waiting"):
        return "Complaint received"
    if "ai processing failed" in lower or "returned to queue" in lower:
        return "Review paused — we will try again shortly"
    if any(m in lower for m in _INTERNAL_NOTE_MARKERS):
        return None

    if lower.startswith("assigned to department:"):
        dept = text.split(":", 1)[-1].strip()
        return f"Sent to {dept}" if dept else "Sent to the municipal team"
    if lower.startswith("worker assigned:"):
        name = text.split(":", 1)[-1].strip()
        return f"Assigned to {name}" if name else "Worker assigned"
    if lower.startswith("routed to "):
        return text[0].upper() + text[1:] if text else text
    if "we only handle:" in lower or "we don't have a department" in lower:
        return text
    if len(text) > 280 and ("(" in text and ")" in text):
        return None
    return text


def _sanitize_status_history(history: list | None, *, role: str | None = None) -> list[dict]:
    out: list[dict] = []
    for entry in history or []:
        if not isinstance(entry, dict):
            continue
        changed_by = entry.get("changed_by")
        note = _public_timeline_note(entry.get("note"))
        out.append(
            {
                "status": _coerce_status(entry.get("status")),
                "changed_by": str(changed_by) if changed_by is not None else "",
                "changed_at": entry.get("changed_at") or datetime.now(timezone.utc),
                "note": note,
            }
        )
    return out


def _sanitize_ai_metadata_for_viewer(ai_meta: dict | None, role: str | None) -> dict | None:
    if not ai_meta or not isinstance(ai_meta, dict):
        return None
    viewer = _normalize_role(role) if role else "citizen"
    routing = ai_meta.get("routing") if isinstance(ai_meta.get("routing"), dict) else {}
    unsupported = bool(ai_meta.get("unsupported_department") or routing.get("unsupported"))

    if viewer == "citizen":
        if unsupported:
            msg = ai_meta.get("public_message") or routing.get("public_message")
            if isinstance(msg, str):
                msg = msg.strip()
            else:
                msg = "This type of issue is not handled through this portal."
            return {
                "unsupported_department": True,
                "public_message": msg,
                "routing": {"unsupported": True, "public_message": msg},
            }
        return None

    if viewer == "officer":
        return None

    if viewer in ("dept_admin", "admin"):
        slim: dict = {}
        if unsupported:
            slim["unsupported_department"] = True
            slim["public_message"] = ai_meta.get("public_message") or routing.get("public_message")
        summary = ai_meta.get("summary")
        if isinstance(summary, str) and summary.strip() and not unsupported:
            slim["summary"] = summary.strip()
        return slim or None

    return None


def _user_can_view_complaint(
    doc: dict,
    *,
    user_id: str,
    role: str,
    department_id: str | None,
) -> bool:
    if role == "admin":
        return True
    if role == "citizen":
        return str(doc.get("citizen_id")) == user_id
    if role == "officer":
        assigned = doc.get("assigned_officer_id")
        return assigned is not None and str(assigned) == user_id
    if role == "dept_admin":
        if not department_id or not doc.get("department_id"):
            return False
        return str(doc["department_id"]) == department_id
    return False

_PRIORITY_RANK_STAGE = {
    "$switch": {
        "branches": [
            {"case": {"$eq": ["$priority", "critical"]}, "then": 0},
            {"case": {"$eq": ["$priority", "high"]}, "then": 1},
            {"case": {"$eq": ["$priority", "medium"]}, "then": 2},
            {"case": {"$eq": ["$priority", "low"]}, "then": 3},
        ],
        "default": 2,
    }
}

_CITIZEN_STATUS_MESSAGES = {
    ComplaintStatus.SUBMITTED.value: "submitted and queued for AI processing",
    ComplaintStatus.AI_PROCESSING.value: "being processed by AI",
    ComplaintStatus.ROUTED_TO_DEPARTMENT.value: "assigned to the responsible department",
    ComplaintStatus.AI_PROCESSED.value: "assigned to the responsible department",
    ComplaintStatus.ASSIGNED.value: "a field worker has been assigned",
    ComplaintStatus.WORK_STARTED.value: "work is in progress",
    ComplaintStatus.RESOLVED.value: "marked as finished",
}


def _citizen_status_message(status: str) -> str:
    return _CITIZEN_STATUS_MESSAGES.get(status, status.replace("_", " "))


async def _notify_citizen_tracking(
    *,
    citizen_id: str,
    complaint_number: str,
    complaint_oid: str,
    status: str,
    extra: str | None = None,
) -> None:
    msg = f"Your complaint {complaint_number} — {_citizen_status_message(status)}."
    if extra:
        msg = f"{msg} {extra}"
    await create_notification(
        user_id=citizen_id,
        notif_type="tracking_update",
        title="Complaint tracking update",
        message=msg,
        complaint_id=complaint_oid,
    )


def _json_safe(value):
    """Recursively convert BSON types for API JSON responses."""
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    return value


def _cloudinary_ready() -> bool:
    settings = get_settings()
    name = (settings.CLOUDINARY_CLOUD_NAME or "").strip()
    if not name or not settings.CLOUDINARY_API_KEY or not settings.CLOUDINARY_API_SECRET:
        return False
    # Cloud name is a short id only (e.g. vtlf6mdk), not a filename or URL
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", name):
        logger.error(
            "Invalid CLOUDINARY_CLOUD_NAME=%r — use the Cloud name from dashboard (Settings → Product environment)",
            name,
        )
        return False
    return True


def _configure_cloudinary() -> None:
    settings = get_settings()
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME.strip(),
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
    )


async def _generate_complaint_id() -> str:
    db = get_database()
    year = datetime.now(timezone.utc).year
    count = await db.complaints.count_documents({})
    return f"HMN-{year}-{count + 1:05d}"


async def _upload_images(images: list[UploadFile]) -> list[dict]:
    settings = get_settings()
    if not _cloudinary_ready():
        logger.warning("Cloudinary not configured or invalid; skipping image upload")
        return []

    _configure_cloudinary()
    uploaded = []

    allowed_ext = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".heif")

    for image in images[: settings.MAX_IMAGES_PER_COMPLAINT]:
        content_type = (image.content_type or "").lower()
        filename = (image.filename or "").lower()
        is_image = content_type.startswith("image/") or any(filename.endswith(ext) for ext in allowed_ext)
        if not is_image:
            logger.warning("Skipping non-image upload: %s (%s)", image.filename, content_type)
            continue

        content = await image.read()
        if not content:
            continue
        if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            logger.warning("Skipping oversized image: %s", image.filename)
            continue
        try:
            result = cloudinary.uploader.upload(
                content,
                folder="civic_complaints",
                resource_type="image",
            )
            uploaded.append({
                "url": result["secure_url"],
                "public_id": result["public_id"],
                "uploaded_at": datetime.now(timezone.utc),
            })
        except Exception as exc:
            # Do not fail the whole complaint — citizen report is more important than photos
            logger.error("Cloudinary upload failed for %s: %s", image.filename, exc)
    return uploaded


async def _notify_department_admins_new_complaint(
    *,
    department_id: str,
    complaint_oid: str,
    complaint_number: str,
    department_name: str,
) -> None:
    db = get_database()
    cursor = db.users.find(
        {
            "role": "dept_admin",
            "department_id": ObjectId(department_id),
            "is_active": True,
        }
    )
    async for admin in cursor:
        await create_notification(
            user_id=str(admin["_id"]),
            notif_type="department_queue",
            title="New complaint routed to your department",
            message=(
                f"{complaint_number} was classified to {department_name}. "
                "Open the complaint and assign an officer."
            ),
            complaint_id=complaint_oid,
        )


def _complaint_create_from_doc(doc: dict) -> ComplaintCreate:
    loc = doc.get("location") or {}
    coords = loc.get("coordinates") or [0.0, 0.0]
    lng = float(coords[0]) if len(coords) > 0 else 0.0
    lat = float(coords[1]) if len(coords) > 1 else 0.0
    return ComplaintCreate(
        title=doc["title"],
        description=doc["description"],
        latitude=lat,
        longitude=lng,
        address=loc.get("address") or "",
    )


async def process_queued_complaint_ai(complaint_id: str) -> dict:
    """BullMQ worker: move submitted → ai_processing, then run Gemini pipeline."""
    db = get_database()
    oid = ObjectId(complaint_id)
    doc = await db.complaints.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    current = doc.get("status")
    if current not in (
        ComplaintStatus.SUBMITTED.value,
        ComplaintStatus.AI_PROCESSING.value,
    ):
        return {"ok": True, "skipped": True, "status": current}

    now = datetime.now(timezone.utc)
    citizen_id = str(doc["citizen_id"])

    if current == ComplaintStatus.SUBMITTED.value:
        await db.complaints.update_one(
            {"_id": oid, "status": ComplaintStatus.SUBMITTED.value},
            {
                "$set": {
                    "status": ComplaintStatus.AI_PROCESSING.value,
                    "updated_at": now,
                },
                "$push": {
                    "status_history": {
                        "status": ComplaintStatus.AI_PROCESSING.value,
                        "changed_by": ObjectId(citizen_id),
                        "changed_at": now,
                        "note": "Review started",
                    }
                },
            },
        )
        doc = await db.complaints.find_one({"_id": oid})
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
        await _notify_citizen_tracking(
            citizen_id=citizen_id,
            complaint_number=doc["complaint_id"],
            complaint_oid=complaint_id,
            status=ComplaintStatus.AI_PROCESSING.value,
        )
        from app.integrations.event_bus import notify_complaint_updated

        await notify_complaint_updated(
            complaint_id=complaint_id,
            status=ComplaintStatus.AI_PROCESSING.value,
            citizen_id=citizen_id,
        )

    await run_ai_job_for_complaint_doc(doc)
    updated = await db.complaints.find_one({"_id": oid}, {"status": 1, "department_id": 1})
    return {
        "ok": True,
        "complaint_id": complaint_id,
        "status": updated.get("status") if updated else None,
    }


async def run_ai_job_for_complaint_doc(doc: dict) -> None:
    """Run Gemini routing + priority for one complaint document (BullMQ worker)."""
    complaint_oid = str(doc["_id"])
    citizen_id = str(doc["citizen_id"])
    complaint_number = doc["complaint_id"]
    data = _complaint_create_from_doc(doc)
    image_urls = [img["url"] for img in doc.get("images", []) if img.get("url")]
    image_count = len(doc.get("images") or [])
    await _process_complaint_ai_job(
        complaint_oid,
        citizen_id,
        data,
        image_urls,
        image_count,
        complaint_number,
    )


async def _process_complaint_ai_job(
    complaint_oid: str,
    citizen_id: str,
    data: ComplaintCreate,
    image_urls: list[str],
    image_count: int,
    complaint_id: str,
) -> None:
    db = get_database()
    try:
        ai_result = await run_ai_pipeline(
            title=data.title,
            description=data.description,
            location={
                "lat": data.latitude,
                "lng": data.longitude,
                "address": data.address,
            },
            complaint_id=complaint_oid,
            image_urls=image_urls,
            image_count=image_count,
        )

        routing = ai_result.get("routing") or {}
        unsupported = bool(ai_result.get("unsupported_department") or routing.get("unsupported"))

        if unsupported:
            public_message = (
                ai_result.get("public_message")
                or routing.get("public_message")
                or "This complaint is not handled by any department on this portal."
            )
            new_status = ComplaintStatus.REJECTED.value
            update_fields: dict = {
                "ai_metadata": ai_result,
                "category": ai_result.get("category", "other"),
                "priority": ai_result.get("predicted_priority", "medium"),
                "status": new_status,
                "updated_at": datetime.now(timezone.utc),
            }
            await db.complaints.update_one(
                {"_id": ObjectId(complaint_oid)},
                {"$set": update_fields, "$unset": {"department_id": ""}},
            )
            await db.complaints.update_one(
                {"_id": ObjectId(complaint_oid)},
                {
                    "$push": {
                        "status_history": {
                            "status": new_status,
                            "changed_by": ObjectId(citizen_id),
                            "changed_at": datetime.now(timezone.utc),
                            "note": public_message,
                        }
                    }
                },
            )
            await append_audit_block(
                complaint_oid,
                ComplaintStatus.AI_PROCESSING.value,
                new_status,
                citizen_id,
                note=public_message,
                metadata={"unsupported_department": True, "category": ai_result.get("category")},
            )
            await _notify_citizen_tracking(
                citizen_id=citizen_id,
                complaint_number=complaint_id,
                complaint_oid=complaint_oid,
                status=new_status,
                extra=public_message,
            )
            from app.integrations.event_bus import notify_complaint_updated

            await notify_complaint_updated(
                complaint_id=complaint_oid,
                status=new_status,
                citizen_id=citizen_id,
                department_id=None,
            )
            return

        dept_label = ai_result.get("predicted_department") or "municipal department"
        new_status = ComplaintStatus.ROUTED_TO_DEPARTMENT.value
        update_fields = {
            "ai_metadata": ai_result,
            "category": ai_result.get("category", "other"),
            "priority": ai_result.get("predicted_priority", "medium"),
            "status": new_status,
            "updated_at": datetime.now(timezone.utc),
        }

        if ai_result.get("department_id"):
            update_fields["department_id"] = ObjectId(ai_result["department_id"])

        await db.complaints.update_one({"_id": ObjectId(complaint_oid)}, {"$set": update_fields})
        await db.complaints.update_one(
            {"_id": ObjectId(complaint_oid)},
            {
                "$push": {
                    "status_history": {
                        "status": new_status,
                        "changed_by": ObjectId(citizen_id),
                        "changed_at": datetime.now(timezone.utc),
                        "note": f"Sent to {dept_label}",
                    }
                }
            },
        )

        await append_audit_block(
            complaint_oid,
            ComplaintStatus.AI_PROCESSING.value,
            new_status,
            citizen_id,
            note=f"Routed to {dept_label}",
            metadata={"category": ai_result.get("category"), "priority": update_fields["priority"]},
        )

        await _notify_citizen_tracking(
            citizen_id=citizen_id,
            complaint_number=complaint_id,
            complaint_oid=complaint_oid,
            status=new_status,
            extra=f"Routed to {dept_label}.",
        )
        from app.integrations.event_bus import notify_complaint_updated

        dept_id = ai_result.get("department_id")
        await notify_complaint_updated(
            complaint_id=complaint_oid,
            status=new_status,
            citizen_id=citizen_id,
            department_id=dept_id,
        )

        if dept_id and not ai_result.get("is_duplicate"):
            await _notify_department_admins_new_complaint(
                department_id=dept_id,
                complaint_oid=complaint_oid,
                complaint_number=complaint_id,
                department_name=ai_result.get("predicted_department") or "your department",
            )

        if not ai_result.get("is_duplicate"):
            try:
                await refresh_clusters_for_location(
                    data.latitude,
                    data.longitude,
                    ai_result.get("category", "other"),
                    exclude_complaint_id=complaint_oid,
                )
            except Exception as cluster_err:
                logger.error("Cluster refresh skipped: %s", cluster_err)
    except Exception as e:
        logger.error("AI processing failed for %s: %s", complaint_id, e)
        now = datetime.now(timezone.utc)
        await db.complaints.update_one(
            {"_id": ObjectId(complaint_oid)},
            {
                "$set": {
                    "status": ComplaintStatus.SUBMITTED.value,
                    "updated_at": now,
                },
                "$unset": {"ai_job_claim": "", "ai_job_claim_expires": ""},
                "$push": {
                    "status_history": {
                        "status": ComplaintStatus.SUBMITTED.value,
                        "changed_by": ObjectId(citizen_id),
                        "changed_at": now,
                        "note": "Review paused — we will try again shortly",
                    }
                },
            },
        )


async def create_complaint(
    data: ComplaintCreate,
    citizen_id: str,
    images: list[UploadFile] | None = None,
) -> ComplaintResponse:
    db = get_database()
    now = datetime.now(timezone.utc)
    complaint_id = await _generate_complaint_id()
    image_docs = await _upload_images(images or [])

    doc = {
        "complaint_id": complaint_id,
        "citizen_id": ObjectId(citizen_id),
        "title": data.title,
        "description": data.description,
        "images": image_docs,
        "location": {
            "type": "Point",
            "coordinates": [data.longitude, data.latitude],
            "address": data.address,
        },
        "status": ComplaintStatus.SUBMITTED.value,
        "priority": "medium",
        "status_history": [
            {
                "status": ComplaintStatus.SUBMITTED.value,
                "changed_by": ObjectId(citizen_id),
                "changed_at": now,
                "note": "Complaint received",
            },
        ],
        "created_at": now,
        "updated_at": now,
    }

    result = await db.complaints.insert_one(doc)
    complaint_oid = result.inserted_id

    await append_audit_block(
        str(complaint_oid),
        None,
        ComplaintStatus.SUBMITTED.value,
        citizen_id,
        note="Complaint submitted",
    )

    import asyncio

    from app.integrations.queue_client import enqueue_complaint_ai

    enqueued = await enqueue_complaint_ai(str(complaint_oid))
    if not enqueued:
        logger.warning(
            "Queue unavailable for %s — processing AI routing in API background",
            complaint_id,
        )

        async def _process_when_queue_down() -> None:
            try:
                await process_queued_complaint_ai(str(complaint_oid))
            except Exception as exc:
                logger.error("In-process AI fallback failed for %s: %s", complaint_id, exc)

        asyncio.create_task(_process_when_queue_down())
    await _notify_citizen_tracking(
        citizen_id=citizen_id,
        complaint_number=complaint_id,
        complaint_oid=str(complaint_oid),
        status=ComplaintStatus.SUBMITTED.value,
        extra="We will update you as it moves through the process.",
    )
    from app.integrations.event_bus import notify_complaint_updated

    await notify_complaint_updated(
        complaint_id=str(complaint_oid),
        status=ComplaintStatus.SUBMITTED.value,
        citizen_id=citizen_id,
    )
    return await get_complaint_by_id(str(complaint_oid))


async def get_complaint_by_id(complaint_id: str) -> ComplaintResponse:
    """Internal use after mutations; does not enforce viewer access."""
    db = get_database()
    complaint = await db.complaints.find_one({"_id": ObjectId(complaint_id)})
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    return await _format_complaint(complaint)


async def get_complaint_for_viewer(
    complaint_id: str,
    *,
    user_id: str,
    role: str,
    department_id: str | None,
) -> ComplaintResponse:
    db = get_database()
    complaint = await db.complaints.find_one({"_id": ObjectId(complaint_id)})
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    role = _normalize_role(role)
    if not _user_can_view_complaint(
        complaint, user_id=user_id, role=role, department_id=department_id
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to view this complaint")
    return await _format_complaint(complaint, role=role)


async def _format_complaint(doc: dict, *, role: str | None = None) -> ComplaintResponse:
    db = get_database()
    dept_name = None
    officer_name = None
    officer_email = None
    officer_phone = None
    citizen_name = None
    citizen_email = None
    citizen_phone = None

    viewer = _normalize_role(role) if role else None

    if doc.get("department_id"):
        dept = await db.departments.find_one({"_id": doc["department_id"]})
        dept_name = dept["name"] if dept else None

    if doc.get("assigned_officer_id"):
        officer = await db.users.find_one(
            {"_id": doc["assigned_officer_id"]},
            {"full_name": 1, "email": 1, "phone": 1},
        )
        if officer:
            officer_name = officer.get("full_name")
            if viewer == "citizen":
                officer_email = officer.get("email")
                officer_phone = officer.get("phone")

    if viewer in ("officer", "dept_admin", "admin") and doc.get("citizen_id"):
        citizen = await db.users.find_one(
            {"_id": doc["citizen_id"]},
            {"full_name": 1, "email": 1, "phone": 1},
        )
        if citizen:
            citizen_name = citizen.get("full_name")
            citizen_email = citizen.get("email")
            citizen_phone = citizen.get("phone")

    raw_ai = _json_safe(doc.get("ai_metadata")) if doc.get("ai_metadata") else None
    ai_meta = _sanitize_ai_metadata_for_viewer(raw_ai if isinstance(raw_ai, dict) else None, role)
    if ai_meta is not None:
        try:
            from app.schemas.complaint import AIMetadataSchema

            ai_meta = AIMetadataSchema.model_validate(ai_meta).model_dump()
        except Exception:
            ai_meta = _sanitize_ai_metadata_for_viewer(
                raw_ai if isinstance(raw_ai, dict) else None, role
            )

    show_category = viewer not in (None, "citizen")

    return ComplaintResponse(
        id=str(doc["_id"]),
        complaint_id=doc["complaint_id"],
        title=doc["title"],
        description=doc["description"],
        images=_sanitize_images(doc.get("images")),
        location=doc.get("location") or {},
        status=_coerce_status(doc.get("status")),
        priority=_coerce_priority(doc.get("priority")),
        category=doc.get("category") if show_category else None,
        department_id=str(doc["department_id"]) if doc.get("department_id") else None,
        department_name=dept_name,
        assigned_officer_id=str(doc["assigned_officer_id"]) if doc.get("assigned_officer_id") else None,
        assigned_officer_name=officer_name,
        assigned_officer_email=officer_email,
        assigned_officer_phone=officer_phone,
        citizen_name=citizen_name,
        citizen_email=citizen_email,
        citizen_phone=citizen_phone,
        ai_metadata=ai_meta,
        resolution=_json_safe(doc.get("resolution")) if doc.get("resolution") else None,
        status_history=_sanitize_status_history(doc.get("status_history"), role=role),
        created_at=doc.get("created_at") or datetime.now(timezone.utc),
        updated_at=doc.get("updated_at") or datetime.now(timezone.utc),
    )


_ASSIGNABLE_STATUSES = (
    ComplaintStatus.ROUTED_TO_DEPARTMENT.value,
    ComplaintStatus.AI_PROCESSED.value,
    ComplaintStatus.VERIFIED.value,
)


async def list_complaints(
    user_id: str,
    role: str,
    page: int = 1,
    limit: int = 20,
    status_filter: str | None = None,
    priority_filter: str | None = None,
    awaiting_assignment: bool = False,
) -> dict:
    db = get_database()
    query: dict = {}
    role = _normalize_role(role)

    if role == "citizen":
        query["citizen_id"] = ObjectId(user_id)
    elif role == "officer":
        query["assigned_officer_id"] = ObjectId(user_id)
    elif role == "dept_admin":
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if user and user.get("department_id"):
            query["department_id"] = user["department_id"]
        else:
            query["_id"] = {"$exists": False}
    elif role == "admin":
        pass  # all complaints city-wide
    else:
        logger.warning("Unknown role %r for list_complaints — returning empty set", role)
        query["_id"] = {"$exists": False}

    if awaiting_assignment:
        query["status"] = {"$in": list(_ASSIGNABLE_STATUSES)}
        query["$or"] = [
            {"assigned_officer_id": {"$exists": False}},
            {"assigned_officer_id": None},
        ]
    elif status_filter:
        query["status"] = status_filter
    if priority_filter:
        query["priority"] = priority_filter

    skip = (page - 1) * limit
    total = await db.complaints.count_documents(query)

    sort_by_priority = role in ("officer", "dept_admin", "admin")
    if sort_by_priority:
        pipeline = [
            {"$match": query},
            {"$addFields": {"priority_rank": _PRIORITY_RANK_STAGE}},
            {"$sort": {"priority_rank": 1, "created_at": -1}},
            {"$skip": skip},
            {"$limit": limit},
        ]
        docs = await _cursor_to_list(db.complaints.aggregate(pipeline), length=limit)
    else:
        cursor = db.complaints.find(query).sort("created_at", -1).skip(skip).limit(limit)
        docs = await _cursor_to_list(cursor, length=limit)
    items: list[ComplaintResponse] = []
    for doc in docs:
        try:
            items.append(await _format_complaint(doc, role=role))
        except Exception as exc:
            logger.warning("Skipping complaint %s in list: %s", doc.get("_id"), exc)

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
    }


async def assign_complaint_officer(
    complaint_id: str,
    officer_id: str,
    actor_id: str,
    actor_role: str,
    actor_department_id: str | None,
) -> ComplaintResponse:
    db = get_database()
    complaint = await db.complaints.find_one({"_id": ObjectId(complaint_id)})
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    officer = await db.users.find_one({"_id": ObjectId(officer_id), "role": "officer", "is_active": True})
    if not officer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Officer not found")

    if actor_role == "dept_admin":
        if not actor_department_id or str(complaint.get("department_id")) != actor_department_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Complaint not in your department")
        if str(officer.get("department_id")) != actor_department_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Officer not in your department")

    if complaint.get("assigned_officer_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complaint already has an assigned officer",
        )
    if complaint.get("status") not in _ASSIGNABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complaint is not ready for officer assignment",
        )

    now = datetime.now(timezone.utc)
    await db.complaints.update_one(
        {"_id": ObjectId(complaint_id)},
        {
            "$set": {
                "assigned_officer_id": ObjectId(officer_id),
                "status": ComplaintStatus.ASSIGNED.value,
                "updated_at": now,
            },
            "$push": {
                "status_history": {
                    "status": ComplaintStatus.ASSIGNED.value,
                    "changed_by": ObjectId(actor_id),
                    "changed_at": now,
                    "note": f"Assigned to {officer['full_name']}",
                }
            },
        },
    )

    await create_notification(
        user_id=officer_id,
        notif_type="assignment",
        title="New case assigned",
        message=f"Complaint {complaint['complaint_id']} — you are the assigned worker.",
        complaint_id=complaint_id,
    )

    await _notify_citizen_tracking(
        citizen_id=str(complaint["citizen_id"]),
        complaint_number=complaint["complaint_id"],
        complaint_oid=complaint_id,
        status=ComplaintStatus.ASSIGNED.value,
        extra=f"Officer {officer['full_name']} will handle your case.",
    )
    from app.integrations.event_bus import notify_complaint_updated

    dept_id = str(complaint["department_id"]) if complaint.get("department_id") else None
    await notify_complaint_updated(
        complaint_id=complaint_id,
        status=ComplaintStatus.ASSIGNED.value,
        citizen_id=str(complaint["citizen_id"]),
        officer_id=officer_id,
        department_id=dept_id,
    )

    return await get_complaint_by_id(complaint_id)


async def _officer_workload_map(department_id: str) -> dict[str, dict]:
    db = get_database()
    dept_oid = ObjectId(department_id)
    pipeline = [
        {
            "$match": {
                "department_id": dept_oid,
                "assigned_officer_id": {"$exists": True, "$ne": None},
                "status": {"$in": _OFFICER_ACTIVE_STATUSES},
            }
        },
        {
            "$group": {
                "_id": "$assigned_officer_id",
                "active_assigned_count": {"$sum": 1},
                "critical_count": {"$sum": {"$cond": [{"$eq": ["$priority", "critical"]}, 1, 0]}},
                "high_count": {"$sum": {"$cond": [{"$eq": ["$priority", "high"]}, 1, 0]}},
                "medium_count": {"$sum": {"$cond": [{"$eq": ["$priority", "medium"]}, 1, 0]}},
                "low_count": {"$sum": {"$cond": [{"$eq": ["$priority", "low"]}, 1, 0]}},
            }
        },
    ]
    out: dict[str, dict] = {}
    async for row in db.complaints.aggregate(pipeline):
        out[str(row["_id"])] = {
            "active_assigned_count": row["active_assigned_count"],
            "critical_count": row["critical_count"],
            "high_count": row["high_count"],
            "medium_count": row["medium_count"],
            "low_count": row["low_count"],
        }
    return out


async def list_department_officers(department_id: str) -> list[dict]:
    db = get_database()
    dept_oid = ObjectId(department_id)
    dept = await db.departments.find_one({"_id": dept_oid}, {"name": 1, "code": 1})
    workload = await _officer_workload_map(department_id)
    cursor = db.users.find(
        {"role": "officer", "department_id": dept_oid, "is_active": True},
        {"password_hash": 0},
    ).sort("full_name", 1)
    officers = []
    async for doc in cursor:
        oid = str(doc["_id"])
        load = workload.get(oid, {})
        service_area = (doc.get("service_area") or "").strip() or None
        officers.append({
            "id": oid,
            "full_name": doc["full_name"],
            "email": doc["email"],
            "phone": doc.get("phone"),
            "service_area": service_area,
            "department_name": dept.get("name") if dept else None,
            "department_code": dept.get("code") if dept else None,
            "active_assigned_count": load.get("active_assigned_count", 0),
            "critical_count": load.get("critical_count", 0),
            "high_count": load.get("high_count", 0),
            "medium_count": load.get("medium_count", 0),
            "low_count": load.get("low_count", 0),
        })
    officers.sort(key=lambda o: (o["active_assigned_count"], o["full_name"].lower()))
    return officers


async def update_complaint_status(
    complaint_id: str,
    new_status: str,
    user_id: str,
    note: str | None = None,
) -> ComplaintResponse:
    db = get_database()
    complaint = await db.complaints.find_one({"_id": ObjectId(complaint_id)})
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    now = datetime.now(timezone.utc)
    history_entry = {
        "status": new_status,
        "changed_by": ObjectId(user_id),
        "changed_at": now,
        "note": note,
    }

    old_status = complaint.get("status")
    if old_status == new_status and not (note or "").strip():
        return await get_complaint_by_id(complaint_id)

    await db.complaints.update_one(
        {"_id": ObjectId(complaint_id)},
        {
            "$set": {"status": new_status, "updated_at": now},
            "$push": {"status_history": history_entry},
        },
    )

    await append_audit_block(
        complaint_id,
        old_status,
        new_status,
        user_id,
        note=note,
    )

    citizen_id = str(complaint["citizen_id"])
    await create_notification(
        user_id=citizen_id,
        notif_type="status_change",
        title="Complaint Status Updated",
        message=f"Your complaint {complaint['complaint_id']} — {_citizen_status_message(new_status)}.",
        complaint_id=complaint_id,
    )

    from app.integrations.event_bus import notify_complaint_updated

    officer_id = str(complaint["assigned_officer_id"]) if complaint.get("assigned_officer_id") else None
    await notify_complaint_updated(
        complaint_id=complaint_id,
        status=new_status,
        citizen_id=citizen_id,
        officer_id=officer_id,
    )

    return await get_complaint_by_id(complaint_id)


async def resolve_complaint(
    complaint_id: str,
    user_id: str,
    notes: str,
) -> ComplaintResponse:
    db = get_database()
    now = datetime.now(timezone.utc)

    complaint_before = await db.complaints.find_one({"_id": ObjectId(complaint_id)})
    old_status = complaint_before.get("status") if complaint_before else None

    await db.complaints.update_one(
        {"_id": ObjectId(complaint_id)},
        {
            "$set": {
                "status": ComplaintStatus.RESOLVED.value,
                "updated_at": now,
                "resolution": {
                    "notes": notes,
                    "resolved_at": now,
                    "resolved_by": ObjectId(user_id),
                },
            },
            "$push": {
                "status_history": {
                    "status": ComplaintStatus.RESOLVED.value,
                    "changed_by": ObjectId(user_id),
                    "changed_at": now,
                    "note": notes,
                }
            },
        },
    )

    await append_audit_block(
        complaint_id,
        old_status,
        ComplaintStatus.RESOLVED.value,
        user_id,
        note=notes,
    )

    complaint = await db.complaints.find_one({"_id": ObjectId(complaint_id)})
    if complaint:
        await create_notification(
            user_id=str(complaint["citizen_id"]),
            notif_type="resolution",
            title="Complaint Resolved",
            message=f"Your complaint {complaint['complaint_id']} has been resolved.",
            complaint_id=complaint_id,
        )

    return await get_complaint_by_id(complaint_id)


async def submit_feedback(
    complaint_id: str,
    citizen_id: str,
    rating: int,
    comment: str | None = None,
) -> dict:
    db = get_database()
    complaint = await db.complaints.find_one({"_id": ObjectId(complaint_id)})
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    if str(complaint["citizen_id"]) != citizen_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your complaint")
    if complaint.get("status") not in ["resolved", "closed"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Complaint not yet resolved")

    existing = await db.feedback.find_one({"complaint_id": ObjectId(complaint_id)})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Feedback already submitted")

    doc = {
        "complaint_id": ObjectId(complaint_id),
        "citizen_id": ObjectId(citizen_id),
        "rating": rating,
        "comment": comment,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.feedback.insert_one(doc)
    await update_complaint_status(
        complaint_id,
        ComplaintStatus.FEEDBACK_RECEIVED.value,
        citizen_id,
        note="Citizen feedback submitted",
    )
    return {"id": str(result.inserted_id), "rating": rating, "comment": comment}


async def get_nearby_complaints(complaint_id: str, radius_m: int = 500) -> list[dict]:
    db = get_database()
    complaint = await db.complaints.find_one({"_id": ObjectId(complaint_id)})
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    coords = complaint.get("location", {}).get("coordinates")
    if not coords:
        return []

    cursor = db.complaints.find(
        {
            "_id": {"$ne": ObjectId(complaint_id)},
            "location": {
                "$nearSphere": {
                    "$geometry": {"type": "Point", "coordinates": coords},
                    "$maxDistance": radius_m,
                }
            },
        }
    ).limit(20)

    items = []
    async for doc in cursor:
        items.append(
            {
                "id": str(doc["_id"]),
                "complaint_id": doc["complaint_id"],
                "title": doc["title"],
                "status": doc["status"],
                "priority": doc.get("priority"),
                "category": doc.get("category"),
                "distance_hint_m": radius_m,
            }
        )
    return items
