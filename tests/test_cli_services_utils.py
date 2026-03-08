"""Tests for service command utility helpers."""

from __future__ import annotations

from pathlib import Path

from phlo.cli.commands.services import utils as service_utils
from phlo.hooks.events import ServiceLifecycleEvent


def test_emit_service_lifecycle_events_preserves_request_correlation(
    monkeypatch,
    tmp_path: Path,
) -> None:
    class RecordingBus:
        def __init__(self) -> None:
            self.events: list[object] = []

        def emit(self, event: object) -> None:
            self.events.append(event)

    bus = RecordingBus()
    monkeypatch.setattr("phlo.hooks.emitters.get_hook_bus", lambda: bus)
    monkeypatch.setattr(
        service_utils, "_resolve_container_name", lambda name, project: f"{project}-{name}"
    )

    service_utils._emit_service_lifecycle_events(
        "pre_start",
        ["postgres", "minio"],
        project_name="demo",
        project_root=tmp_path,
        request_id="req-123",
        metadata={"native": False},
    )

    lifecycle_events = [event for event in bus.events if isinstance(event, ServiceLifecycleEvent)]
    assert len(lifecycle_events) == 2
    assert {event.service_name for event in lifecycle_events} == {"postgres", "minio"}
    assert {event.correlation.request_id for event in lifecycle_events} == {"req-123"}
    assert all(event.phase == "pre_start" for event in lifecycle_events)
