from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, HTTPException, status

from app.auth.jwt import authenticate_user, create_access_token
from app.config import settings
from app.models.schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Authenticate and get JWT access token.

    Default users:
    - admin / admin123 (admin role)
    - analyst / analyst123 (analyst role)
    """
    user = authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT token
    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(
        data={
            "sub": user["username"],
            "user_id": user["user_id"],
            "email": user["email"],
            "role": user["role"],
        },
        expires_delta=access_token_expires,
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user={
            "user_id": user["user_id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
        },
    )
