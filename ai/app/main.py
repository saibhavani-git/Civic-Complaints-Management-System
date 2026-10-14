"""Humanizr AI microservice — optional standalone FastAPI deployment."""

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.pipeline import run_pipeline

app = FastAPI(title="Humanizr AI Service", version="1.0.0")


class PipelineRequest(BaseModel):
    title: str = Field(min_length=5)
    description: str = Field(min_length=20)
    latitude: float
    longitude: float
    complaint_id: str
    image_count: int = 0


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/api/v1/pipeline")
async def pipeline(payload: PipelineRequest):
    return await run_pipeline(
        title=payload.title,
        description=payload.description,
        location={"lat": payload.latitude, "lng": payload.longitude},
        complaint_id=payload.complaint_id,
        image_count=payload.image_count,
    )
