"""Opaque cursor pagination helpers for API list envelopes."""

from __future__ import annotations

import base64
import json
from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")


def encode_cursor(offset: int) -> str:
    payload = json.dumps({"offset": max(0, offset)}, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("ascii")


def decode_cursor(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        payload = json.loads(base64.urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return 0
    offset = payload.get("offset", 0)
    return offset if isinstance(offset, int) and offset >= 0 else 0


def paginate_items(
    items: Sequence[T], *, limit: int, cursor: str | None = None
) -> tuple[list[T], str | None]:
    safe_limit = max(1, min(limit, 500))
    offset = decode_cursor(cursor)
    page = list(items[offset : offset + safe_limit])
    next_offset = offset + len(page)
    next_cursor = encode_cursor(next_offset) if next_offset < len(items) else None
    return page, next_cursor
