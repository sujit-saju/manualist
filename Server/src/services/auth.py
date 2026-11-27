import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from src.core.security import hash_password, verify_password
from src.repositories.refresh_tokens import (
    consume_refresh_token,
    insert_refresh_token,
    revoke_refresh_token,
)
from src.repositories.users import find_user_by_id, find_user_credentials, insert_user
from src.schemas.auth import RegisterResponse


class DuplicateEmailError(Exception):
    """Raised when a duplicate email is found in the database."""


class InvalidCredentialsError(Exception):
    """Raised when an account cannot authenticate."""


@dataclass(frozen=True)
class RefreshSession:
    user_id: UUID
    expires_at: datetime
    token: str = field(repr=False)


def _hash_refresh_token(token: str) -> str:
    return sha256(token.encode()).hexdigest()


async def _store_refresh_session(
    connection: AsyncConnection, user_id: UUID, expires_at: datetime
) -> RefreshSession:
    token = token_urlsafe(32)
    await insert_refresh_token(
        connection,
        token_id=uuid4(),
        user_id=user_id,
        token_hash=_hash_refresh_token(token),
        expires_at=expires_at,
    )
    return RefreshSession(user_id=user_id, expires_at=expires_at, token=token)


async def create_refresh_session(
    engine: AsyncEngine, user_id: UUID, ttl_days: int
) -> RefreshSession:
    async with engine.begin() as connection:
        expires_at = datetime.now(UTC) + timedelta(days=ttl_days)
        return await _store_refresh_session(connection, user_id, expires_at)


async def rotate_refresh_session(engine: AsyncEngine, token: str) -> RefreshSession:
    async with engine.begin() as connection:
        previous = await consume_refresh_token(connection, _hash_refresh_token(token))
        if previous is None:
            raise InvalidCredentialsError
        user_id, expires_at = previous
        return await _store_refresh_session(connection, user_id, expires_at)


async def revoke_refresh_session(engine: AsyncEngine, token: str) -> None:
    """End the refresh session identified by the presented token."""
    async with engine.begin() as connection:
        await revoke_refresh_token(connection, _hash_refresh_token(token))


async def register_user(
    engine: AsyncEngine, email: str, password: str
) -> RegisterResponse:
    """Create a user and return the public registration fields."""
    user_id = uuid4()
    password_hash = await asyncio.to_thread(hash_password, password)
    async with engine.begin() as connection:
        inserted = await insert_user(
            connection=connection,
            user_id=user_id,
            email=email,
            password_hash=password_hash,
        )

        if not inserted:
            raise DuplicateEmailError(f"Email {email} already exists.")

    return RegisterResponse(id=user_id, email=email)


async def login_user(
    engine: AsyncEngine, email: str, password: str, dummy_password_hash: str
) -> UUID:
    """Verify the credentials and return the authenticated user's ID."""
    async with engine.begin() as connection:
        credentials = await find_user_credentials(connection, email)

        password_hash = (
            credentials.password_hash if credentials else dummy_password_hash
        )
        password_matches = await asyncio.to_thread(
            verify_password, password, password_hash
        )
        if credentials is None or not credentials.is_active or not password_matches:
            raise InvalidCredentialsError

    return credentials.id


async def get_current_user(engine: AsyncEngine, user_id: UUID) -> RegisterResponse:
    """Return the public details of an active user."""
    async with engine.connect() as connection:
        email = await find_user_by_id(connection, user_id)

    if email is None:
        raise InvalidCredentialsError

    return RegisterResponse(id=user_id, email=email)
