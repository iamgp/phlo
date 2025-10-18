from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings


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


# Create limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.rate_limit_default],
    storage_uri="memory://",
)
