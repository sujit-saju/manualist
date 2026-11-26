"""Check API documentation availability by environment."""

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import create_app


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("environment", "expected_status"), [("development", 200), ("production", 404)]
)
async def test_api_docs_by_environment(
    monkeypatch: pytest.MonkeyPatch, environment: str, expected_status: int
) -> None:
    """Expose generated documentation only outside production."""
    monkeypatch.setenv("APP_ENV", environment)
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for path in ("/openapi.json", "/docs", "/redoc"):
            response = await client.get(path)
            assert response.status_code == expected_status, path
