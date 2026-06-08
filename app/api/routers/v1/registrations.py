from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database.db import get_db
from app.schemas.registration import UserRegistration, UserResponse
from app.api.controllers.v1.regitsration import AuthService


router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    responses={
        201: {"description": "User registered successfully"},
        409: {"description": "Email or contact already exists"},
        422: {"description": "Validation error"},
    },
)
async def register(
    payload: UserRegistration,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user.

    - **email**: Valid email address (must be unique)
    - **name**: Full name (letters and spaces only)
    - **contact**: Indian mobile number in format +91-XXXXXXXXXX
    - **role_id**: 1 = Admin, 2 = Learner
    - **password**: Min 8 chars, must have upper, lower, digit, special char
    """

    try:
        user = await AuthService.register_user(db=db, payload=payload)
        return user

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    except Exception as e:
        logger.error(f"Unexpected error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong. Please try again.",
        )