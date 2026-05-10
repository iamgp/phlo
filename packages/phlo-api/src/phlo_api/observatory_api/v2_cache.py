"""Shared Observatory v2 read model cache helpers."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ReadModelCache:
    """Small TTL cache scoped by project and read model name."""

    project_key: Callable[[], str]
    _values: dict[tuple[str, str], tuple[float, Any]] = field(default_factory=dict)
    _lock: threading.RLock = field(default_factory=threading.RLock)

    def cached(self, name: str, ttl_seconds: float, loader: Callable[[], Any]) -> Any:
        key = (self.project_key(), name)
        now = time.monotonic()

        with self._lock:
            cached = self._values.get(key)
            if cached is not None:
                expires_at, value = cached
                if expires_at > now:
                    return value

            value = loader()
            self._values[key] = (time.monotonic() + ttl_seconds, value)
            return value

    def clear(self) -> None:
        with self._lock:
            self._values.clear()
