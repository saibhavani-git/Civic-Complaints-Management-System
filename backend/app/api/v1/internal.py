from fastapi import APIRouter, Header, HTTPException, status

from app.config import get_settings
from app.services.complaint_service import process_queued_complaint_ai

router = APIRouter(prefix="/internal", tags=["Internal"])


def _verify_internal_key(x_internal_key: str | None) -> None:
    expected = get_settings().INTERNAL_API_KEY
    if not expected or x_internal_key != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal key")


@router.post("/complaints/{complaint_id}/process-ai")
async def internal_process_complaint_ai(
    complaint_id: str,
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
):
    """BullMQ worker entrypoint: submitted → AI processing → routed to department."""
    _verify_internal_key(x_internal_key)
    return await process_queued_complaint_ai(complaint_id)
