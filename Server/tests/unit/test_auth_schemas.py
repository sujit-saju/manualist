from uuid import UUID

import pytest
from pydantic_core import ValidationError

from src.schemas.auth import RegisterRequest, RegisterResponse


def test_accepts_password_at_minimum_length() -> None:
    request = RegisterRequest(email="alice@example.com", password="a" * 15)

    assert request.email == "alice@example.com"
    assert request.password == "a" * 15

def test_rejects_password_below_minimum_length() -> None:
    with pytest.raises(ValidationError) as exc_info:
        RegisterRequest(email="alice@example.com", password="a" * 14)

    assert exc_info.value.errors()[0]["loc"] == ("password",)

def test_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError) as exc_info:
        RegisterRequest(email="not-an-email", password="a" * 15)

    assert exc_info.value.errors()[0]["loc"] == ("email",)

def test_registration_response_exposes_only_public_fields() -> None:
    user_id = UUID("f7e84fa2-d09a-4e18-abac-dd52c3512520")
    response = RegisterResponse(id=user_id, email="alice@example.com")

    assert response.model_dump(mode="json") == {
        "id": str(user_id),
        "email": "alice@example.com",
    }