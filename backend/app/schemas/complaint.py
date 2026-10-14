from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ComplaintStatus(str, Enum):
    SUBMITTED = "submitted"
    AI_PROCESSING = "ai_processing"
    ROUTED_TO_DEPARTMENT = "routed_to_department"
    AI_PROCESSED = "ai_processed"  # legacy; same stage as routed_to_department
    VERIFIED = "verified"
    ASSIGNED = "assigned"
    WORK_STARTED = "work_started"
    RESOLVED = "resolved"
    FEEDBACK_RECEIVED = "feedback_received"
    # Legacy values kept for existing records
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"
    REJECTED = "rejected"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LocationSchema(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    address: str = Field(min_length=5)


class ComplaintCreate(BaseModel):
    title: str = Field(min_length=5, max_length=200)
    description: str = Field(min_length=20, max_length=5000)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    address: str = Field(min_length=5)


class ImageSchema(BaseModel):
    url: str
    public_id: str = ""
    uploaded_at: Optional[datetime] = None


class AIMetadataSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    summary: Optional[str] = None
    category: Optional[str] = None
    category_confidence: Optional[float] = None
    predicted_department: Optional[str] = None
    predicted_priority: Optional[str] = None
    confidence_score: Optional[float] = None
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None
    similarity_score: Optional[float] = None
    image_verification: Optional[dict] = None
    model_comparison: Optional[list] = None
    routing: Optional[dict] = None
    model_versions: Optional[dict] = None
    processed_at: Optional[datetime] = None


class StatusHistoryEntry(BaseModel):
    status: ComplaintStatus
    changed_by: str
    changed_at: datetime
    note: Optional[str] = None


class ResolutionSchema(BaseModel):
    notes: str = Field(min_length=10)
    proof_image_urls: list[str] = []


class ComplaintResponse(BaseModel):
    id: str
    complaint_id: str
    title: str
    description: str
    images: list[ImageSchema] = []
    location: dict
    status: ComplaintStatus
    priority: Priority
    category: Optional[str] = None
    department_id: Optional[str] = None
    department_name: Optional[str] = None
    assigned_officer_id: Optional[str] = None
    assigned_officer_name: Optional[str] = None
    assigned_officer_email: Optional[str] = None
    assigned_officer_phone: Optional[str] = None
    citizen_name: Optional[str] = None
    citizen_email: Optional[str] = None
    citizen_phone: Optional[str] = None
    ai_metadata: Optional[AIMetadataSchema] = None
    resolution: Optional[dict] = None
    status_history: list[StatusHistoryEntry] = []
    created_at: datetime
    updated_at: datetime


class ComplaintStatusUpdate(BaseModel):
    status: ComplaintStatus
    note: Optional[str] = None


class ComplaintListResponse(BaseModel):
    items: list[ComplaintResponse]
    total: int
    page: int
    limit: int
    pages: int
