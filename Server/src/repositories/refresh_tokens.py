"""Database operations for refresh sessions."""

from datetime import datetime
from typing import cast
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


async def insert_refresh_token(
    connection: AsyncConnection,
    *,
    token_id: UUID,
    user_id: UUID,
    token_hash: str,
    expires_at: datetime,
) -> None:
    await connection.execute(
        text("""
            INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at)
            VALUES (:token_id, :user_id, :token_hash, :expires_at)
            """),
        {
            "token_id": token_id,
            "user_id": user_id,
            "token_hash": token_hash,
            "expires_at": expires_at,
        },
    )


async def consume_refresh_token(
    connection: AsyncConnection, token_hash: str
) -> tuple[UUID, datetime] | None:
    """Revoke a usable token and return the session it belonged to."""
    result = await connection.execute(
        text("""
            UPDATE refresh_tokens AS token
            SET revoked_at = clock_timestamp(), updated_at = clock_timestamp()
            WHERE token.token_hash = :token_hash
              AND token.revoked_at IS NULL
              AND token.expires_at > clock_timestamp()
              AND EXISTS (
                  SELECT 1 FROM users
                  WHERE users.id = token.user_id AND users.is_active
              )
            RETURNING token.user_id, token.expires_at
            """),
        {"token_hash": token_hash},
    )
    row = result.one_or_none()
    if row is None:
        return None

    user_id, expires_at = row
    return cast(UUID, user_id), cast(datetime, expires_at)


async def revoke_refresh_token(connection: AsyncConnection, token_hash: str) -> None:
    """Revoke the presented token if it is still unrevoked."""
    await connection.execute(
        text("""
            UPDATE refresh_tokens
            SET revoked_at = clock_timestamp(), updated_at = clock_timestamp()
            WHERE token_hash = :token_hash AND revoked_at IS NULL
            """),
        {"token_hash": token_hash},
    )
