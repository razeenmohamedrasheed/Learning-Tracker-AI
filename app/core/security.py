from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt

from app.config.config import settings


# -------------------------------------------------------
# OOP CONCEPT: ENCAPSULATION
# All JWT logic is locked inside this module.
# Routes and services never touch jose directly —
# they just call create_access_token() or decode_token().
# -------------------------------------------------------

def create_access_token(data: dict) -> tuple[str, int]:
    """
    Create a short-lived JWT access token.
    Returns (token_string, expires_in_seconds)
    """
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    expire     = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        **data,
        "exp":  expire,
        "type": "access",
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, expires_in


def create_refresh_token(data: dict) -> tuple[str, datetime]:
    """
    Create a long-lived JWT refresh token.
    Returns (token_string, expires_at_datetime)
    """
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        **data,
        "exp":  expires_at,
        "type": "refresh",
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, expires_at


def decode_token(token: str) -> dict:
    """
    Decode and verify a JWT token.
    Raises JWTError if invalid or expired.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])