from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from jose import JWTError
from loguru import logger

from app.crud.registration import get_user_by_email
from app.crud.tokens import (
    save_refresh_token,
    get_refresh_token,
    revoke_refresh_token,
    revoke_all_user_tokens,
)
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.schemas.tokens import LoginRequest, TokenResponse
from app.utils.password_utility import verify_password


class LoginService:

    @staticmethod
    async def login(
        db: AsyncSession,
        payload: LoginRequest,
    ) -> TokenResponse:
        """
        Login flow:
        1. Find user by email
        2. Verify password
        3. Check account is active
        4. Generate access + refresh tokens
        5. Save refresh token to DB
        """
        logger.info(f"Login attempt: {payload.email}")

        # Step 1 — find user
        user = await get_user_by_email(db, payload.email)
        if not user:
            raise ValueError("Invalid email or password")

        # Step 2 — verify password
        if not verify_password(payload.password, user.password_hash):
            raise ValueError("Invalid email or password")

        # Step 3 — check active
        if not user.is_active:
            raise ValueError("Account is disabled. Contact support.")

        # Step 4 — generate tokens
        token_data    = {"sub": user.user_id, "role": user.role_id}
        access_token,  expires_in = create_access_token(token_data)
        refresh_token, expires_at = create_refresh_token(token_data)

        await revoke_all_user_tokens(db, user.user_id)
        # Step 5 — save refresh token
        await save_refresh_token(
            db         = db,
            user_id    = user.user_id,
            raw_token  = refresh_token,
            expires_at = expires_at,
        )

        logger.info(f"Login successful: {user.user_id}")

        return TokenResponse(
            access_token  = access_token,
            refresh_token = refresh_token,
            expires_in    = expires_in,
        )

    @staticmethod
    async def refresh_access_token(
        db: AsyncSession,
        raw_refresh_token: str,
    ) -> TokenResponse:
        """
        Refresh flow (token rotation):
        1. Decode + validate JWT
        2. Check token in DB (not revoked)
        3. Check not expired
        4. Issue new access + refresh tokens
        5. Revoke old refresh token
        6. Save new refresh token
        """
        # Step 1 — decode
        try:
            payload = decode_token(raw_refresh_token)
            if payload.get("type") != "refresh":
                raise ValueError("Invalid token type")
        except JWTError:
            raise ValueError("Invalid or expired refresh token")

        # Step 2 — check DB
        db_token = await get_refresh_token(db, raw_refresh_token)
        if not db_token:
            raise ValueError("Refresh token not found or already revoked")

        # Step 3 — check expiry
        if db_token.expires_at < datetime.now(timezone.utc):
            raise ValueError("Refresh token expired. Please login again.")

        # Step 4 — generate new tokens
        token_data    = {"sub": payload["sub"], "role": payload["role"]}
        access_token,  expires_in = create_access_token(token_data)
        refresh_token, expires_at = create_refresh_token(token_data)

        # Step 5 — revoke old
        await revoke_refresh_token(db, raw_refresh_token)

        # Step 6 — save new
        await save_refresh_token(
            db         = db,
            user_id    = payload["sub"],
            raw_token  = refresh_token,
            expires_at = expires_at,
        )

        logger.info(f"Token refreshed: {payload['sub']}")

        return TokenResponse(
            access_token  = access_token,
            refresh_token = refresh_token,
            expires_in    = expires_in,
        )

    @staticmethod
    async def logout(
        db: AsyncSession,
        raw_refresh_token: str,
    ) -> None:
        """Revoke current session's refresh token."""
        revoked = await revoke_refresh_token(db, raw_refresh_token)
        if not revoked:
            raise ValueError("Token not found or already revoked")
        logger.info("Logout — token revoked")

    @staticmethod
    async def logout_all(
        db: AsyncSession,
        user_id: str,
    ) -> None:
        """Revoke ALL sessions for a user (logout from all devices)."""
        await revoke_all_user_tokens(db, user_id)
        logger.info(f"All sessions revoked: {user_id}")