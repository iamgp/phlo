"""Service identity helpers for service-to-service calls.

When phlo-api calls Dagster or Trino, it should identify itself
with a short-lived HMAC service token, not a spoofable header.

Token format: <service_id>:<timestamp>:<nonce>:<hmac>
where hmac = HMAC-SHA256(secret, service_id + ":" + timestamp + ":" + nonce)

The nonce (UUID4) prevents replay of intercepted tokens within the
validity window. The shared secret comes from PHLO_SERVICE_SECRET env var.

Header conventions for request chain attribution:
    Authorization: Bearer <service-token>   (service identity)
    X-Phlo-Initiator: alice@example.com     (originating user)
    X-Phlo-Correlation-Id: <request-id>     (audit correlation)
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time
from uuid import uuid4

from phlo.logging import get_logger

logger = get_logger(__name__)

PHLO_SERVICE_SECRET_ENV = "PHLO_SERVICE_SECRET"
PHLO_INITIATOR_HEADER = "X-Phlo-Initiator"
PHLO_CORRELATION_HEADER = "X-Phlo-Correlation-Id"

DEFAULT_MAX_AGE_SECONDS = 300


def create_service_token(service_id: str) -> str:
    """Create a short-lived HMAC service token with a nonce.

    Args:
        service_id: Name of the service (e.g., "phlo-api").

    Returns:
        Token string suitable for Bearer authorization.

    Raises:
        RuntimeError: If PHLO_SERVICE_SECRET is not set.
    """
    secret = os.environ.get(PHLO_SERVICE_SECRET_ENV)
    if not secret:
        raise RuntimeError(f"{PHLO_SERVICE_SECRET_ENV} must be set for service-to-service auth")

    timestamp = str(int(time.time()))
    nonce = uuid4().hex
    message = f"{service_id}:{timestamp}:{nonce}"
    signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()

    return f"{service_id}:{timestamp}:{nonce}:{signature}"


def validate_service_token(
    token: str,
    max_age_seconds: int = DEFAULT_MAX_AGE_SECONDS,
) -> str | None:
    """Validate an HMAC service token.

    Args:
        token: Token string in format "service_id:timestamp:nonce:hmac".
        max_age_seconds: Maximum token age in seconds (default 5 minutes).

    Returns:
        service_id if valid, None if invalid.
    """
    secret = os.environ.get(PHLO_SERVICE_SECRET_ENV)
    if not secret:
        return None

    parts = token.split(":", 3)
    if len(parts) != 4:
        # Reject legacy 3-part tokens
        return None

    service_id, timestamp_str, nonce, provided_hmac = parts

    try:
        token_time = int(timestamp_str)
    except ValueError:
        return None

    if abs(time.time() - token_time) > max_age_seconds:
        return None

    message = f"{service_id}:{timestamp_str}:{nonce}"
    expected = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, provided_hmac):
        return None

    return service_id


def build_service_headers(
    service_id: str,
    initiator: str | None = None,
    correlation_id: str | None = None,
) -> dict[str, str]:
    """Build HTTP headers for an authenticated service-to-service call.

    Args:
        service_id: Name of the calling service.
        initiator: Originating user principal, if applicable.
        correlation_id: Request/run ID for audit correlation.

    Returns:
        Dict of header name → value.

    Raises:
        RuntimeError: If PHLO_SERVICE_SECRET is not set.
    """
    token = create_service_token(service_id)
    headers: dict[str, str] = {
        "Authorization": f"Bearer {token}",
    }
    if initiator:
        headers[PHLO_INITIATOR_HEADER] = initiator
    if correlation_id:
        headers[PHLO_CORRELATION_HEADER] = correlation_id
    return headers
