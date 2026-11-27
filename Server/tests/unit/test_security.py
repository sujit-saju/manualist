from argon2 import PasswordHasher

from src.core.security import hash_password, verify_password


def test_hash_can_be_verified_with_original_password() -> None:
    password = "demo password for local testing"

    encoded_hash = hash_password(password)

    assert PasswordHasher().verify(encoded_hash, password)

def test_verify_password_accepts_match_and_rejects_mismatch() -> None:
    password = "demo password for local testing"
    password_hash = hash_password(password)

    assert verify_password(password, password_hash) is True
    assert verify_password("a different password", password_hash) is False