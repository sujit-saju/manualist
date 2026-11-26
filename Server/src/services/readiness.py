"""Connectivity checks for the services needed by the API."""

import asyncio
from collections.abc import Awaitable

import httpx
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from src.core.config import Settings


class OllamaModelsMissingError(Exception):
    """The configured models are absent from the Ollama instance."""


async def _postgres_ready(url: str) -> bool:
    engine = create_async_engine(url, poolclass=NullPool)
    try:
        async with engine.connect() as connection:
            result = await connection.scalar(text("SELECT 1"))
            return isinstance(result, int) and result == 1
    finally:
        await engine.dispose()


async def _redis_ready(url: str) -> bool:
    client = Redis.from_url(url)
    async with client:
        return bool(await client.ping())


def _model_tag(name: str) -> str:
    return name if ":" in name.rsplit("/", 1)[-1] else f"{name}:latest"


async def _ollama_ready(url: str, models: set[str]) -> bool:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{url.rstrip('/')}/api/tags")
        response.raise_for_status()
        payload = response.json()
    entries = payload.get("models") if isinstance(payload, dict) else None
    if not isinstance(entries, list):
        return False
    available = {
        _model_tag(entry["name"])
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("name"), str)
    }
    if not models <= available:
        raise OllamaModelsMissingError
    return True


async def _check(probe: Awaitable[bool] | None, timeout_seconds: float) -> str:
    if probe is None:
        return "not_configured"
    try:
        async with asyncio.timeout(timeout_seconds):
            return "ok" if await probe else "unavailable"
    except OllamaModelsMissingError:
        return "models_missing"
    except (OSError, SQLAlchemyError, RedisError, httpx.HTTPError, ValueError):
        return "unavailable"


async def check_dependencies(settings: Settings) -> dict[str, str]:
    """Report bounded connectivity checks without exposing connection strings."""
    models = {
        _model_tag(model)
        for model in (
            settings.embedding_model,
            settings.llm_model,
            settings.query_rewrite_model,
        )
        if model
    }
    probes = {
        "postgres": _postgres_ready(str(settings.database_url))
        if settings.database_url
        else None,
        "redis": _redis_ready(str(settings.redis_url)) if settings.redis_url else None,
        "ollama": (
            _ollama_ready(str(settings.ollama_base_url), models)
            if settings.ollama_base_url
            and settings.embedding_model
            and settings.llm_model
            else None
        ),
    }
    statuses = await asyncio.gather(
        *(
            _check(probe, settings.readiness_timeout_seconds)
            for probe in probes.values()
        )
    )
    return dict(zip(probes, statuses, strict=True))
