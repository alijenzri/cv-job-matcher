"""
Production middleware stack for CV-Job Matcher API.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import time
import logging
import uuid

logger = logging.getLogger("api.middleware")


class TimingMiddleware(BaseHTTPMiddleware):
    """Adds X-Process-Time and X-Request-ID headers to every response."""

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        logger.info(f"[{request_id}] {request.method} {request.url.path}")

        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"[{request_id}] Unhandled error: {e}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "request_id": request_id}
            )

        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        response.headers["X-Request-ID"] = request_id

        logger.info(f"[{request_id}] {response.status_code} ({process_time:.4f}s)")
        return response
