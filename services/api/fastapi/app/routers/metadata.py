# metadata.py - FastAPI router for metadata and system information endpoints
# Provides health checks, cache statistics, and user information
# without requiring access to sensitive data

from typing import Any

from fastapi import APIRouter

from app.auth.dependencies import CurrentUser
from app.middleware.cache import get_cache_stats

# --- Router Configuration ---
# Metadata and system information router
router = APIRouter(prefix="/metadata", tags=["Metadata"])


# --- Metadata Endpoints ---
# System information and diagnostics endpoints
@router.get("/health", summary="API health check")
async def health_check() -> dict[str, str]:
    """Health check endpoint (no auth required)."""
    return {"status": "healthy", "service": "phlo-api"}


@router.get("/cache/stats", summary="Cache statistics")
async def cache_stats(current_user: CurrentUser) -> dict[str, Any]:
    """Get in-memory cache statistics."""
    return get_cache_stats()


@router.get("/user/me", summary="Get current user info")
async def get_current_user_info(current_user: CurrentUser) -> dict[str, Any]:
    """Get information about the currently authenticated user."""
    return {
        "user_id": current_user.get("user_id"),
        "username": current_user.get("sub"),
        "email": current_user.get("email"),
        "role": current_user.get("role"),
    }
