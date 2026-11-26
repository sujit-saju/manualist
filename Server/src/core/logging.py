"""Structured request logging."""

import re
from time import perf_counter
from uuid import uuid4

import structlog
from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger()
REQUEST_ID_HEADER = "X-Request-ID"
SAFE_REQUEST_ID = re.compile(r"[A-Za-z0-9._-]{1,128}")


def configure_logging() -> None:
    """Render application events as JSON with UTC timestamps."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
    )


async def log_request(request: Request, call_next: RequestResponseEndpoint) -> Response:
    """Assign a request ID and log the resulting HTTP status."""
    incoming_id = request.headers.get(REQUEST_ID_HEADER, "")
    request_id = incoming_id if SAFE_REQUEST_ID.fullmatch(incoming_id) else uuid4().hex
    request.state.request_id = request_id
    started = perf_counter()
    with structlog.contextvars.bound_contextvars(request_id=request_id):
        try:
            response = await call_next(request)
        except Exception:
            logger.error("request_failed", method=request.method, status_code=500)
            raise
        response.headers[REQUEST_ID_HEADER] = request_id
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            latency_ms=round((perf_counter() - started) * 1000, 2),
        )
    return response
