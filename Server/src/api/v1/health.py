"""Health endpoints for the Manualist API."""

from typing import cast

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from src.core.config import Settings
from src.services.readiness import check_dependencies

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def liveness() -> dict[str, str]:
    """Report that the API process is serving requests."""
    return {"status": "ok"}


@router.get(
    "/ready", response_model=None, responses={503: {"description": "Unavailable"}}
)
async def readiness(request: Request) -> dict[str, str] | JSONResponse:
    """Report whether PostgreSQL, Redis, and the Ollama models are available."""
    checks = await check_dependencies(cast(Settings, request.app.state.settings))
    if all(result == "ok" for result in checks.values()):
        return {"status": "ok"}
    return JSONResponse(
        status_code=503,
        content={
            "error": {
                "code": "DEPENDENCIES_UNAVAILABLE",
                "message": "API is not ready",
                "details": checks,
                "request_id": request.state.request_id,
            }
        },
    )
