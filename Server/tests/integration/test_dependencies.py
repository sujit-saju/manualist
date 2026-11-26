"""Check readiness reporting and exercise live infrastructure when configured."""

import os

import httpx
import pytest

from src.core.config import Settings
from src.services import readiness


@pytest.mark.asyncio
async def test_dependencies_without_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Report each missing dependency distinctly from a healthy connection."""
    for name in ("DATABASE_URL", "REDIS_URL", "OLLAMA_BASE_URL"):
        monkeypatch.delenv(name, raising=False)

    assert await readiness.check_dependencies(Settings()) == {
        "postgres": "not_configured",
        "redis": "not_configured",
        "ollama": "not_configured",
    }


@pytest.mark.asyncio
async def test_live_postgres_and_redis(monkeypatch: pytest.MonkeyPatch) -> None:
    """Send actual SELECT and PING commands to the CI services."""
    database_url = os.getenv("TEST_DATABASE_URL")
    redis_url = os.getenv("TEST_REDIS_URL")
    if not database_url or not redis_url:
        pytest.skip("Set TEST_DATABASE_URL and TEST_REDIS_URL to test real services")
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("REDIS_URL", redis_url)
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)

    report = await readiness.check_dependencies(Settings())
    assert report["postgres"] == report["redis"] == "ok"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("configured_model", "expected"), [("chat", "ok"), ("missing", "models_missing")]
)
async def test_ollama_model_check(
    monkeypatch: pytest.MonkeyPatch, configured_model: str, expected: str
) -> None:
    """Read Ollama's model list through HTTP without calling an inference service."""
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama.test")
    monkeypatch.setenv("LLM_MODEL", configured_model)
    monkeypatch.setenv("EMBEDDING_MODEL", "embed")
    monkeypatch.delenv("QUERY_REWRITE_MODEL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)

    def model_list(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/tags"
        return httpx.Response(
            200, json={"models": [{"name": "chat:latest"}, {"name": "embed:latest"}]}
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(model_list))
    monkeypatch.setattr(httpx, "AsyncClient", lambda: client)

    assert (await readiness.check_dependencies(Settings()))["ollama"] == expected


@pytest.mark.asyncio
async def test_connection_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    """Translate refused local connections into dependency status."""
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://localhost:1/test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:1/0")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:1")
    monkeypatch.setenv("LLM_MODEL", "chat")
    monkeypatch.setenv("EMBEDDING_MODEL", "embed")

    assert await readiness.check_dependencies(Settings()) == {
        "postgres": "unavailable",
        "redis": "unavailable",
        "ollama": "unavailable",
    }
