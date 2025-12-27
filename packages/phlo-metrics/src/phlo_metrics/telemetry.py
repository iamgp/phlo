"""Telemetry recording helpers for hook-based metrics."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from phlo.hooks import TelemetryEvent


class TelemetryRecorder:
    def __init__(self, path: Path | None = None, max_bytes: int = 20_000_000) -> None:
        """Create a recorder that writes telemetry events to JSONL."""

        self.path = path or _default_path()
        self.max_bytes = max_bytes

    def record(self, event: TelemetryEvent) -> None:
        """Append a telemetry event to the JSONL file, rotating if needed."""

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._rotate_if_needed()
        payload = _serialize_event(event)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, default=str) + "\n")

    def _rotate_if_needed(self) -> None:
        """Rotate the telemetry file when it exceeds max_bytes."""

        if not self.path.exists():
            return
        if self.path.stat().st_size < self.max_bytes:
            return
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        rotated = self.path.with_name(f"{self.path.stem}.{timestamp}{self.path.suffix}")
        self.path.rename(rotated)


def _default_path() -> Path:
    """Return the default telemetry output path."""

    env_path = os.environ.get("PHLO_TELEMETRY_PATH")
    if env_path:
        return Path(env_path)
    return Path.cwd() / ".phlo" / "telemetry" / "events.jsonl"


def _serialize_event(event: TelemetryEvent) -> dict[str, Any]:
    """Serialize a TelemetryEvent into JSON-friendly primitives."""

    payload = asdict(event)
    payload["timestamp"] = event.timestamp.isoformat()
    return payload
