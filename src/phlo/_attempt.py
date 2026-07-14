"""Shared validation for positive execution-attempt correlation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def normalize_attempt(value: Any) -> int:
    """Return a positive integer attempt or reject malformed retry metadata."""
    if isinstance(value, bool):
        raise ValueError("attempt must be a positive integer")
    if isinstance(value, int):
        attempt = value
    elif isinstance(value, str) and value.strip():
        try:
            attempt = int(value)
        except ValueError as exc:
            raise ValueError("attempt must be a positive integer") from exc
    else:
        raise ValueError("attempt must be a positive integer")
    if attempt <= 0:
        raise ValueError("attempt must be a positive integer")
    return attempt


def attempt_from_tags(tags: Mapping[str, str]) -> tuple[int | None, str | None]:
    """Parse an optional retry tag without aliasing invalid values to attempt one."""
    raw_attempt = tags.get("phlo/attempt")
    if raw_attempt is None:
        return 1, None
    try:
        return normalize_attempt(raw_attempt), None
    except ValueError:
        return None, "invalid_attempt"
