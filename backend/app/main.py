import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import admin, analytics, audit, auth, clusters, complaints, events, internal, notifications, staff
from app.config import get_settings
from app.db.database import close_db, connect_db, get_database
from app.db.init_db import create_indexes, seed_departments
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_settings.cache_clear()
    await connect_db()
    db = get_database()
    await create_indexes(db)
    await seed_departments(db)
    logger.info("Database connected and initialized (AI jobs via BullMQ queue service)")

    async def _startup_queue_recovery() -> None:
        await asyncio.sleep(4)
        try:
            from app.services.complaint_queue_recovery import recover_stale_complaints

            n = await recover_stale_complaints()
            if n:
                logger.info("Startup: re-enqueued %s stale complaint(s) for AI routing", n)
        except Exception as exc:
            logger.warning("Startup queue recovery skipped: %s", exc)

    asyncio.create_task(_startup_queue_recovery())

    yield

    await close_db()
    logger.info("Database connection closed")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Humanizr API",
        description="AI-powered smart civic complaint management and municipal decision support",
        version="1.0.1",
        lifespan=lifespan,
    )

    origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(complaints.router, prefix="/api/v1")
    app.include_router(notifications.router, prefix="/api/v1")
    app.include_router(admin.router, prefix="/api/v1")
    app.include_router(analytics.router, prefix="/api/v1")
    app.include_router(clusters.router, prefix="/api/v1")
    app.include_router(audit.router, prefix="/api/v1")
    app.include_router(staff.router, prefix="/api/v1")
    app.include_router(internal.router, prefix="/api/v1")
    app.include_router(events.router, prefix="/api/v1")
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logging.getLogger(__name__).exception("Unhandled error on %s", request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc) or "Internal server error"},
        )

    @app.get("/health")
    async def health_check():
        from app.integrations.queue_client import queue_service_reachable

        db_ok = False
        try:
            db = get_database()
            await db.command("ping")
            db_ok = True
        except Exception:
            pass
        queue_ok = await queue_service_reachable()
        now_utc = datetime.now(timezone.utc).isoformat()
        body = {
            "status": "healthy" if db_ok and queue_ok else "degraded",
            "db": "connected" if db_ok else "disconnected",
            "queue": "reachable" if queue_ok else "unreachable",
            "server_time_utc": now_utc,
            "version": app.version,
        }
        return body

    return app


app = create_app()
