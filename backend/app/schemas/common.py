from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=2)
    code: str = Field(min_length=2, max_length=10)
    description: Optional[str] = None
    keywords: list[str] = []


class DepartmentResponse(BaseModel):
    id: str
    name: str
    code: str
    description: Optional[str] = None
    keywords: list[str] = []
    head_officer_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime


class FeedbackCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)


class FeedbackResponse(BaseModel):
    id: str
    complaint_id: str
    citizen_id: str
    rating: int
    comment: Optional[str] = None
    created_at: datetime


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    complaint_id: Optional[str] = None
    is_read: bool
    created_at: datetime


class AnalyticsOverview(BaseModel):
    total_complaints: int
    pending: int
    in_progress: int
    resolved: int
    avg_resolution_hours: float
    priority_distribution: dict[str, int]
    resolution_rate: float
