import uuid
import hashlib
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.tokens import RefreshToken


# -------------------------------------------------------
# Helper — hash the raw token before storing
# We store the HASH not the raw token (same idea as password hashing).
# If DB is compromised, attacker can't use the hashed tokens.
# -------------------------------------------------------
def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


async def save_refresh_token(
    db: AsyncSession,
    user_id: str,
    raw_token: str,
    expires_at: datetime,
) -> RefreshToken:
    """Hash and save a new refresh token for a user."""
    token = RefreshToken(
        id         = str(uuid.uuid4()),
        user_id    = user_id,
        token_hash = hash_token(raw_token),
        expires_at = expires_at,
    )
    db.add(token)
    await db.flush()
    return token


async def get_refresh_token(
    db: AsyncSession,
    raw_token: str,
) -> RefreshToken | None:
    """Find a refresh token by its raw value (hashes it first)."""
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_token(raw_token),
            RefreshToken.is_revoked == False,
        )
    )
    return result.scalars().first()


async def revoke_refresh_token(
    db: AsyncSession,
    raw_token: str,
) -> bool:
    """Mark a refresh token as revoked (logout)."""
    token = await get_refresh_token(db, raw_token)
    if not token:
        return False
    token.is_revoked = True
    await db.flush()
    return True


async def revoke_all_user_tokens(
    db: AsyncSession,
    user_id: str,
) -> None:
    """Revoke ALL refresh tokens for a user (logout from all devices)."""
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id   == user_id,
            RefreshToken.is_revoked == False,
        )
    )
    tokens = result.scalars().all()
    for token in tokens:
        token.is_revoked = True
    await db.flush()