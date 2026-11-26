"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from src.api.v1.health import router as health_router
from src.core.config import Settings
from src.core.logging import configure_logging, log_request


def create_app() -> FastAPI:
    """Create the API application and register its routes."""
    settings = Settings()
    configure_logging()
    openapi_url = None if settings.app_env == "production" else "/openapi.json"
    app = FastAPI(title="Manualist", openapi_url=openapi_url)
    app.state.settings = settings
    app.include_router(health_router, prefix="/api/v1")
    app.add_middleware(BaseHTTPMiddleware, dispatch=log_request)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )
    return app
