# rate_limit.py - Rate limiting middleware configuration using SlowAPI
# Implements role-based rate limiting for API endpoints to prevent abuse
# and ensure fair resource allocation across different user types

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings


# --- Rate Limiting Functions ---
# Functions for role-based rate limit determination
def get_user_role_from_request(request):
    """Extract user role from request for role-based rate limiting."""
    # Default to most restrictive limit
    if not hasattr(request.state, "user"):
        return settings.rate_limit_default

    user = request.state.user
    role = user.get("role", "analyst")

    if role == "admin":
        return settings.rate_limit_admin
    elif role == "analyst":
        return settings.rate_limit_analyst
    else:
        return settings.rate_limit_default


# --- Limiter Configuration ---
# Global rate limiter instance using in-memory storage
# Create limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.rate_limit_default],
    storage_uri="memory://",
)
