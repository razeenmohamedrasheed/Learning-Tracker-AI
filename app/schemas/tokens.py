from pydantic import BaseModel, EmailStr, Field

class LoginRequest(BaseModel):
    """What the client sends to /login"""
    email:    EmailStr
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    """What we return after successful login/refresh"""
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    expires_in:    int  # access token TTL in seconds


class RefreshRequest(BaseModel):
    """What the client sends to /refresh"""
    refresh_token: str


class MessageResponse(BaseModel):
    """Generic success message"""
    message: str