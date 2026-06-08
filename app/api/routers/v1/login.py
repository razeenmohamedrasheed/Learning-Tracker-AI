from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database.db import get_db
from app.schemas.tokens import LoginRequest, TokenResponse, RefreshRequest, MessageResponse
from app.api.controllers.v1.login  import LoginService


router = APIRouter()


# -------------------------------------------------------
# POST /api/v1/auth/login
# -------------------------------------------------------
@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login and get access + refresh tokens",
)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await LoginService.login(db=db, payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


# -------------------------------------------------------
# POST /api/v1/auth/refresh
# -------------------------------------------------------
@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Get new access token using refresh token",
)
async def refresh(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await LoginService.refresh_access_token(
            db=db,
            raw_refresh_token=payload.refresh_token,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error(f"Refresh error: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")


# -------------------------------------------------------
# POST /api/v1/auth/logout
# -------------------------------------------------------
@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout — revoke current session",
)
async def logout(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        await LoginService.logout(db=db, raw_refresh_token=payload.refresh_token)
        return MessageResponse(message="Logged out successfully")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# -------------------------------------------------------
# POST /api/v1/auth/logout-all
# -------------------------------------------------------
@router.post(
    "/logout-all",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout from all devices",
)
async def logout_all(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        from app.core.security import decode_token
        token_data = decode_token(payload.refresh_token)
        await LoginService.logout_all(db=db, user_id=token_data["sub"])
        return MessageResponse(message="Logged out from all devices")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Logout failed")