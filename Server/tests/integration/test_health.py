"""HTTP checks for the health endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.v1 import health
from src.core.config import Settings
from src.main import create_app


@pytest.mark.asyncio
async def test_liveness() -> None:
    """Return a successful response at the versioned liveness route."""
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_liveness_returns_unique_request_ids() -> None:
    """Return a successful response at the versioned liveness route."""
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response1 = await client.get("/api/v1/health/live")
        response2 = await client.get("/api/v1/health/live")

    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response1.headers["X-Request-ID"] != response2.headers["X-Request-ID"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("dependency_status", "expected_status"), [("ok", 200), ("unavailable", 503)]
)
async def test_readiness(
    monkeypatch: pytest.MonkeyPatch,
    dependency_status: str,
    expected_status: int,
) -> None:
    """Translate the dependency report into an HTTP response."""

    async def fake_ready(_settings: Settings) -> dict[str, str]:
        return {"postgres": dependency_status, "redis": "ok", "ollama": "ok"}

    monkeypatch.setattr(health, "check_dependencies", fake_ready)
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/health/ready", headers={"X-Request-ID": "test-ready"}
        )

    assert response.status_code == expected_status
    assert response.headers["X-Request-ID"] == "test-ready"
    if expected_status == 200:
        assert response.json() == {"status": "ok"}
    else:
        error = response.json()["error"]
        assert error["details"]["postgres"] == "unavailable"
        assert error["request_id"] == "test-ready"
