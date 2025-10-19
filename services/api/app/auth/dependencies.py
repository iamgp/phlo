# dependencies.py - FastAPI authentication dependencies for JWT-based access control
# Defines dependency injection functions for user authentication and role-based authorization
# Provides type-annotated dependencies for route handlers

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt import decode_access_token

# --- Security Scheme ---
# HTTP Bearer token authentication scheme
security = HTTPBearer()


# --- Authentication Dependencies ---
# FastAPI dependency functions for user authentication and authorization
async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> dict:
    """Get the current authenticated user from JWT token."""
    token = credentials.credentials

    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    return payload


async def get_admin_user(current_user: Annotated[dict, Depends(get_current_user)]) -> dict:
    """Require admin role."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


# --- Type Aliases ---
# Convenient type aliases for dependency injection in route handlers
CurrentUser = Annotated[dict, Depends(get_current_user)]
AdminUser = Annotated[dict, Depends(get_admin_user)]
