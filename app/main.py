import sys
import asyncio

# ── Windows Asyncio Fix ───────────────────────────────────────────
# This MUST be at the very top to prevent 'NotImplementedError' on Windows.
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from celery import Celery

from app.config import settings
from app.api.routes import router
from app.api.middleware import TimingMiddleware

import sys
import asyncio

# ── Windows Sync Issue Fix ─────────────────────────────────────────
# Fix for 'NotImplementedError' when using subprocesses (Playwright) on Windows.
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# ── Logging ────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


# ── Celery ─────────────────────────────────────────────────────────

def make_celery(app_name: str = __name__) -> Celery:
    celery = Celery(
        app_name,
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND
    )
    celery.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
    )
    return celery

celery_app = make_celery()


# ── FastAPI Lifespan ───────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("🚀 CV-Job Matcher API starting up...")
    logger.info(f"   Environment: {settings.APP_ENV}")
    logger.info(f"   Database: {settings.DATABASE_URL[:30]}...")
    logger.info(f"   Celery Broker: {settings.CELERY_BROKER_URL}")

    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Verify loop type (should be ProactorEventLoop on Windows)
    loop = asyncio.get_running_loop()
    logger.info(f"   Active Event Loop: {type(loop).__name__}")

    yield

    logger.info("🛑 CV-Job Matcher API shutting down...")


# ── FastAPI App ────────────────────────────────────────────────────

app = FastAPI(
    title="CV-Job Matcher API",
    description="Enterprise-grade CV-to-Job matching engine with RAG, hybrid search, and PII redaction.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(TimingMiddleware)

# API routes
app.include_router(router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "CV-Job Matcher API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.APP_PORT)
