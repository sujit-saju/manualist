import os
from uuid import UUID, uuid4

import httpx
import pytest


def test_registration_flow() -> None:
    base_url = os.getenv("MANUALIST_TEST_API_URL")
    if not base_url:
        pytest.skip("Set MANUALIST_TEST_API_URL to run against the local API.")

    email = f"registration-{uuid4().hex}@example.com"
    password = "demo password for registration tests"
    path = "/api/v1/auth/register"

    with httpx.Client(base_url=base_url) as client:
        created = client.post(path, json={"email": email, "password": password})
        assert created.status_code == 201
        body = created.json()
        assert set(body) == {"id", "email"}
        assert body["email"] == email
        UUID(body["id"])

        duplicate = client.post(
            path, json={"email": email.upper(), "password": password}
        )
        assert duplicate.status_code == 409
        assert duplicate.json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"

        invalid = client.post(path, json={"email": email, "password": "too-short"})
        assert invalid.status_code == 422
        error = invalid.json()["error"]
        assert error["code"] == "VALIDATION_ERROR"
        assert error["request_id"] == invalid.headers["X-Request-ID"]
        assert {"location": ["body", "password"], "type": "string_too_short"} in (
            error["details"]["fields"]
        )
        assert "too-short" not in invalid.text