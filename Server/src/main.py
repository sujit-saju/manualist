"""FastAPI application factory."""

import asyncio
from secrets import token_urlsafe
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.v1.health import router as health_router
from src.api.v1.auth import router as auth_router
from src.core.config import Settings
from src.core.logging import configure_logging, log_request
from src.core.security import hash_password


def create_app() -> FastAPI:
    """Create the API application and register its routes."""
    settings = Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        database_url = settings.database_url
        app.state.dummy_password_hash = await asyncio.to_thread(
            hash_password, token_urlsafe(32)
        )
        engine = create_async_engine(str(database_url)) if database_url else None
        app.state.db_engine = engine
        try:
            yield
        finally:
            if engine is not None:
                await engine.dispose()

    configure_logging()
    openapi_url = None if settings.app_env == "production" else "/openapi.json"
    app = FastAPI(
        title="Manualist",
        openapi_url=openapi_url,
        lifespan=lifespan,
    )
    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": {
                        "fields": [
                            {"location": list(error["loc"]), "type": error["type"]}
                            for error in exc.errors()
                        ]
                    },
                    "request_id": request.state.request_id,
                }
            },
        )
    app.state.settings = settings
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
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
