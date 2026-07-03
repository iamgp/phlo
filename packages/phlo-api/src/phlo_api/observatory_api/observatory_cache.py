"""Shared Observatory read model cache helpers."""

from __future__ import annotations

from pathlib import Path
import pickle
import sqlite3
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ReadModelCache:
    """Small TTL cache scoped by project and read model name."""

    project_key: Callable[[], str]
    db_path: Callable[[], Path] | None = None
    _values: dict[tuple[str, str], tuple[float, Any]] = field(default_factory=dict)
    _lock: threading.RLock = field(default_factory=threading.RLock)

    def cached(self, name: str, ttl_seconds: float, loader: Callable[[], Any]) -> Any:
        project = self.project_key()
        key = (project, name)
        now = time.monotonic()
        epoch_now = time.time()

        with self._lock:
            cached = self._values.get(key)
            if cached is not None:
                expires_at, value = cached
                if expires_at > now:
                    return value

            stored = self._load_stored(project, name, epoch_now)
            if stored is not None:
                expires_at, value = stored
                self._values[key] = (now + max(0, expires_at - epoch_now), value)
                return value

            value = loader()
            expires_at = time.time() + ttl_seconds
            self._values[key] = (time.monotonic() + ttl_seconds, value)
            self._store(project, name, expires_at, value)
            return value

    def clear(self) -> None:
        with self._lock:
            self._values.clear()
            path = self._db_path()
            if path is None or not path.exists():
                return
            with sqlite3.connect(path) as connection:
                connection.execute("delete from read_models")

    def _db_path(self) -> Path | None:
        if self.db_path is None:
            return None
        return self.db_path()

    def _connect(self) -> sqlite3.Connection | None:
        path = self._db_path()
        if path is None:
            return None
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path)
        connection.execute(
            """
            create table if not exists read_models (
              project_key text not null,
              name text not null,
              expires_at real not null,
              payload blob not null,
              primary key (project_key, name)
            )
            """
        )
        return connection

    def _load_stored(self, project: str, name: str, now: float) -> tuple[float, Any] | None:
        connection = self._connect()
        if connection is None:
            return None
        with connection:
            row = connection.execute(
                "select expires_at, payload from read_models where project_key = ? and name = ?",
                (project, name),
            ).fetchone()
            if row is None:
                return None
            expires_at = float(row[0])
            if expires_at <= now:
                connection.execute(
                    "delete from read_models where project_key = ? and name = ?",
                    (project, name),
                )
                return None
            try:
                return expires_at, pickle.loads(row[1])
            except Exception:
                connection.execute(
                    "delete from read_models where project_key = ? and name = ?",
                    (project, name),
                )
                return None

    def _store(self, project: str, name: str, expires_at: float, value: Any) -> None:
        connection = self._connect()
        if connection is None:
            return
        # ponytail: local cache only; switch to typed JSON rows if this leaves one machine.
        try:
            payload = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception:
            return
        with connection:
            connection.execute(
                """
                insert into read_models(project_key, name, expires_at, payload)
                values (?, ?, ?, ?)
                on conflict(project_key, name)
                do update set expires_at = excluded.expires_at, payload = excluded.payload
                """,
                (project, name, expires_at, payload),
            )
