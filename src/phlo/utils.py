"""Common utility functions for Phlo."""

from __future__ import annotations

from typing import Any


def compact_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Remove None values from a dictionary."""
    return {k: v for k, v in d.items() if v is not None}
