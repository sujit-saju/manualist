import os
from uuid import uuid4

import httpx
import pytest


def test_refresh_rotates_cookie_and_logout_revokes_it() -> None:
    base_url = os.getenv("MANUALIST_TEST_API_URL")
    if not base_url:
        pytest.skip("Set MANUALIST_TEST_API_URL to run against the local API.")

    credentials = {
        "email": f"refresh-{uuid4().hex}@example.com",
        "password": "demo password for refresh tests",
    }
    cookie_name = "manualist_refresh"
    refresh_path = "/api/v1/auth/refresh"
    with httpx.Client(base_url=base_url) as client:
        assert client.post(refresh_path).status_code == 401
        registered = client.post("/api/v1/auth/register", json=credentials)
        assert registered.status_code == 201
        login = client.post("/api/v1/auth/login", json=credentials)
        assert login.status_code == 200
        old_token = client.cookies[cookie_name]
        assert "httponly" in login.headers["set-cookie"].lower()

        refreshed = client.post(refresh_path)
        assert refreshed.status_code == 200
        assert client.cookies[cookie_name] != old_token
        assert refreshed.headers["cache-control"] == "no-store"
        access_token = refreshed.json()["access_token"]
        profile = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
        )
        assert profile.status_code == 200
        assert profile.json() == registered.json()

        with httpx.Client(
            base_url=base_url, cookies={cookie_name: old_token}
        ) as replay:
            rejected = replay.post(refresh_path)
        assert rejected.status_code == 401
        assert rejected.json()["error"]["code"] == "INVALID_REFRESH_TOKEN"

        current_token = client.cookies[cookie_name]
        logout_path = "/api/v1/auth/logout"
        logged_out = client.post(logout_path)
        assert logged_out.status_code == 204
        assert logged_out.content == b""
        assert cookie_name not in client.cookies
        assert client.post(logout_path).status_code == 204
        assert client.post(refresh_path).status_code == 401

        with httpx.Client(
            base_url=base_url, cookies={cookie_name: current_token}
        ) as replay:
            assert replay.post(refresh_path).status_code == 401
            assert replay.post(logout_path).status_code == 204
