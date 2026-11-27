import jwt
from datetime import UTC, datetime, timedelta
from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Return an encoded Argon2id hash for a password."""
    return _password_hasher.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    """Check a submitted password against the stored Argon2 hash."""
    try:
        return _password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False

def create_access_token(user_id: UUID, secret_key: str, ttl_minutes: int) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(user_id),
            "iat": now,
            "exp": now + timedelta(minutes=ttl_minutes),
        },
        secret_key,
        algorithm="HS256"
    )

def decode_access_token(token: str, secret_key: str) -> UUID:
    payload = jwt.decode(
        token,
        secret_key,
        algorithms=["HS256"],
        options={"require": ["sub", "iat", "exp"]},
    )
    return UUID(payload["sub"])
