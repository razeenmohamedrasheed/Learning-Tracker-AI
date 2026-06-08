# app/core/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError
from loguru import logger

from app.database.db import get_db
from app.core.security import decode_token
from app.crud.registration import get_user_by_id
from app.models.registration import User


bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Protected route dependency.

    Flow:
    1. Read Bearer token from Authorization header
    2. Decode and validate JWT
    3. Check token type is "access"
    4. Fetch user from DB
    5. Check user is active
    6. Return user object to the route

    Usage in any protected route:
        current_user: User = Depends(get_current_user)
    """

    # Reusable 401 exception
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Step 1 — check header exists
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Step 2 — decode JWT
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        logger.warning("JWT decode failed — invalid or expired token")
        raise credentials_exception

    # Step 3 — check token type (must be access token, not refresh)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Step 4 — get user_id from token
    user_id: str = payload.get("sub")
    if not user_id:
        raise credentials_exception

    # Step 5 — fetch user from DB
    user = await get_user_by_id(db, user_id)
    if not user:
        logger.warning(f"Token valid but user not found: {user_id}")
        raise credentials_exception

    # Step 6 — check active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled. Contact support.",
        )

    return user

def require_role(role_id: int):
    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role_id != role_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this resource",
            )
        return current_user
    return role_checker