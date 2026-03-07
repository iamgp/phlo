"""Tests for maintenance API capability resolution."""

from __future__ import annotations

from datetime import datetime, timezone

from phlo_api.api import maintenance


class _Operation:
    operation = "optimize"
    namespace = "raw"
    ref = "main"
    status = "success"
    completed_at = datetime(2026, 3, 7, tzinfo=timezone.utc)
    duration_seconds = 12.5
    tables_processed = 3
    errors = 0
    snapshots_deleted = 0
    orphan_files = 0
    total_records = 42
    total_size_mb = 10.0
    dry_run = False
    run_id = "run-1"
    job_name = "optimize_tables_job"


class _Snapshot:
    last_updated = datetime(2026, 3, 7, tzinfo=timezone.utc)
    operations = [_Operation()]


class _ReadModel:
    def load_maintenance_status(self):
        return _Snapshot()

    def render_maintenance_prometheus(self) -> str:
        return "phlo_metric 1\n"


def test_get_maintenance_status_uses_capability(monkeypatch) -> None:
    """Maintenance status should come from the neutral read-model capability."""
    monkeypatch.setattr(maintenance, "_resolve_maintenance_read_model", lambda: _ReadModel())

    payload = maintenance.get_maintenance_status()

    assert isinstance(payload, maintenance.MaintenanceStatusSnapshot)
    assert payload.operations[0].operation == "optimize"


def test_get_maintenance_metrics_uses_capability(monkeypatch) -> None:
    """Prometheus maintenance metrics should come from the neutral read-model capability."""
    monkeypatch.setattr(maintenance, "_resolve_maintenance_read_model", lambda: _ReadModel())

    response = maintenance.get_maintenance_metrics()

    assert response.status_code == 200
    assert response.body.decode() == "phlo_metric 1\n"
