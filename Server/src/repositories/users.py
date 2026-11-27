from typing import cast
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection
from dataclasses import dataclass


@dataclass(frozen=True)
class UserCredentials:
    id: UUID
    password_hash: str
    is_active: bool


async def insert_user(
    connection: AsyncConnection,
    user_id: UUID,
    email: str,
    password_hash: str,
) -> bool:
    """Insert a user and report whether a row was created."""
    statement = text("""
        INSERT INTO users (id, email, password_hash)
        VALUES (:user_id, :email, :password_hash)
        ON CONFLICT ON CONSTRAINT uq_users_email DO NOTHING
        RETURNING id
        """)
    result = await connection.execute(
        statement,
        {
            "user_id": user_id,
            "email": email,
            "password_hash": password_hash,
        },
    )
    return result.scalar_one_or_none() is not None


async def find_user_credentials(
    connection: AsyncConnection, email: str
) -> UserCredentials | None:
    """Fetch the fields needed to check a login attempt."""

    result = await connection.execute(
        text("""
            SELECT id, password_hash, is_active
            FROM users
            WHERE email = CAST(:email AS citext)
            """),
        {"email": email},
    )
    row = result.one_or_none()
    if row is None:
        return None

    user_id, password_hash, is_active = row
    return UserCredentials(
        id=user_id,
        password_hash=password_hash,
        is_active=is_active,
    )

async def find_user_by_id(
    connection: AsyncConnection, user_id: UUID
) -> str | None:
    """Return the email for an active user."""
    result = await connection.execute(
        text(
            """
            SELECT email
            FROM users
            WHERE id = :user_id AND is_active = true
            """
        ),
        {"user_id": user_id},
    )
    email = result.scalar_one_or_none()
    return cast(str | None, email)