"""Tests for WAP (Write-Audit-Publish) lifecycle sensors."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import dagster as dg

from phlo_dagster.wap_sensors import (
    _all_checks_passed,
    _wap_branch_name,
    wap_auto_promotion_sensor,
    wap_branch_creation_sensor,
    wap_branch_cleanup_sensor,
    write_wap_report,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def test_wap_branch_name():
    assert _wap_branch_name("abc123") == "pipeline-run-abc123"


def test_wap_sensors_default_to_running() -> None:
    assert wap_branch_creation_sensor.default_status == dg.DefaultSensorStatus.RUNNING
    assert wap_auto_promotion_sensor.default_status == dg.DefaultSensorStatus.RUNNING
    assert wap_branch_cleanup_sensor.default_status == dg.DefaultSensorStatus.RUNNING


def test_write_wap_report_updates_run_json(monkeypatch, tmp_path):
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))

    write_wap_report("run-1", status="branch_created", branch="pipeline-run-1")
    write_wap_report(
        "run-1",
        status="promoted",
        branch="pipeline-run-1",
        source_hash="source",
        target_hash_before="before",
        target_hash_after="after",
    )

    payload = json.loads((tmp_path / ".phlo" / "wap-reports" / "run-1.json").read_text())
    assert payload["status"] == "promoted"
    assert payload["branch"] == "pipeline-run-1"
    assert payload["target_hash_after"] == "after"
    assert payload["run_id"] == "run-1"
    assert payload["created_at"]


def test_write_wap_report_keeps_identity_fields_and_ignores_write_failure(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))

    write_wap_report(
        "run-1",
        schema_version="wrong",
        updated_at="wrong",
        status="branch_created",
    )

    payload = json.loads((tmp_path / ".phlo" / "wap-reports" / "run-1.json").read_text())
    assert payload["run_id"] == "run-1"
    assert payload["schema_version"] == "phlo.wap_report.v1"
    assert payload["updated_at"] != "wrong"

    def raise_write_error(*args, **kwargs):
        raise OSError("disk unavailable")

    monkeypatch.setattr("pathlib.Path.write_text", raise_write_error)
    write_wap_report("run-2", status="branch_created")


# ---------------------------------------------------------------------------
# _all_checks_passed
# ---------------------------------------------------------------------------


class _FakeCheckEvaluation:
    def __init__(self, passed: bool):
        self.passed = passed


class _FakeEvent:
    def __init__(self, passed: bool):
        self.asset_check_evaluation = _FakeCheckEvaluation(passed)


class _FakeRecord:
    def __init__(self, passed: bool):
        self.event_log_entry = _FakeEvent(passed)


def test_all_checks_passed_no_events():
    """No check events means nothing failed — returns True."""
    instance = MagicMock()
    instance.get_records_for_run.return_value = MagicMock(records=[])
    assert _all_checks_passed(instance, "run-1") is True


def test_all_checks_passed_all_pass():
    """All checks passing returns True."""
    instance = MagicMock()
    instance.get_records_for_run.return_value = MagicMock(
        records=[
            _FakeRecord(passed=True),
            _FakeRecord(passed=True),
        ]
    )
    assert _all_checks_passed(instance, "run-1") is True


def test_all_checks_passed_one_fails():
    """A single failing check returns False."""
    instance = MagicMock()
    instance.get_records_for_run.return_value = MagicMock(
        records=[
            _FakeRecord(passed=True),
            _FakeRecord(passed=False),
        ]
    )
    assert _all_checks_passed(instance, "run-1") is False


# ---------------------------------------------------------------------------
# NessieResource.create_branch / merge_branch
# ---------------------------------------------------------------------------


class TestNessieResourceBranchOps:
    """Unit tests for NessieResource create_branch and merge_branch."""

    def _make_resource(self):
        from phlo_nessie.resource import NessieResource

        return NessieResource(base_url="http://localhost:19120")

    @patch("phlo_nessie.resource.requests")
    def test_create_branch_success(self, mock_requests):
        """create_branch returns hash on success."""
        nessie = self._make_resource()

        # get_branch_hash for source
        mock_get = MagicMock()
        mock_get.status_code = 200
        mock_get.json.return_value = {"hash": "abc123"}

        # create_branch POST
        mock_post = MagicMock()
        mock_post.status_code = 200
        mock_post.json.return_value = {"hash": "def456"}

        mock_requests.get.return_value = mock_get
        mock_requests.post.return_value = mock_post

        result = nessie.create_branch("pipeline-run-1", from_ref="main")
        assert result == "def456"
        mock_requests.post.assert_called_once()

    @patch("phlo_nessie.resource.requests")
    def test_create_branch_source_missing(self, mock_requests):
        """create_branch returns None when source ref doesn't exist."""
        nessie = self._make_resource()

        mock_get = MagicMock()
        mock_get.status_code = 404
        mock_get.json.return_value = {}
        mock_requests.get.return_value = mock_get

        result = nessie.create_branch("pipeline-run-1", from_ref="nonexistent")
        assert result is None

    @patch("phlo_nessie.resource.requests")
    def test_merge_branch_success(self, mock_requests):
        """merge_branch returns True on success."""
        nessie = self._make_resource()

        source_get = MagicMock()
        source_get.status_code = 200
        source_get.json.return_value = {"hash": "source-hash"}

        target_get = MagicMock()
        target_get.status_code = 200
        target_get.json.return_value = {"hash": "main-hash"}

        mock_post = MagicMock()
        mock_post.status_code = 200

        mock_requests.get.side_effect = [source_get, target_get]
        mock_requests.post.return_value = mock_post

        result = nessie.merge_branch(source="pipeline-run-1", target="main")
        assert result is True
        merge_url = mock_requests.post.call_args.args[0]
        assert merge_url.endswith("/api/v2/trees/main@main-hash/history/merge")
        assert mock_requests.post.call_args.kwargs["json"]["fromHash"] == "source-hash"
        assert "params" not in mock_requests.post.call_args.kwargs

    @patch("phlo_nessie.resource.requests")
    def test_merge_branch_conflict(self, mock_requests):
        """merge_branch returns False on conflict."""
        nessie = self._make_resource()

        source_get = MagicMock()
        source_get.status_code = 200
        source_get.json.return_value = {"hash": "source-hash"}

        target_get = MagicMock()
        target_get.status_code = 200
        target_get.json.return_value = {"hash": "main-hash"}

        mock_post = MagicMock()
        mock_post.status_code = 409

        mock_requests.get.side_effect = [source_get, target_get]
        mock_requests.post.return_value = mock_post

        result = nessie.merge_branch(source="pipeline-run-1", target="main")
        assert result is False
        merge_url = mock_requests.post.call_args.args[0]
        assert merge_url.endswith("/api/v2/trees/main@main-hash/history/merge")
        assert mock_requests.post.call_args.kwargs["json"]["fromHash"] == "source-hash"
        assert "params" not in mock_requests.post.call_args.kwargs

    @patch("phlo_nessie.resource.requests")
    def test_delete_branch_uses_branch_endpoint(self, mock_requests):
        """delete_branch uses the Nessie branch delete endpoint."""
        nessie = self._make_resource()

        branch_get = MagicMock()
        branch_get.status_code = 200
        branch_get.json.return_value = {"hash": "branch-hash"}

        delete_response = MagicMock()
        delete_response.status_code = 204

        mock_requests.get.return_value = branch_get
        mock_requests.delete.return_value = delete_response

        result = nessie.delete_branch("pipeline-run-1")

        assert result is True
        delete_url = mock_requests.delete.call_args.args[0]
        assert delete_url.endswith("/api/v1/trees/branch/pipeline-run-1")
        assert mock_requests.delete.call_args.kwargs["params"] == {"expectedHash": "branch-hash"}


# ---------------------------------------------------------------------------
# get_wap_definitions
# ---------------------------------------------------------------------------


def test_get_wap_definitions_returns_three_sensors():
    """get_wap_definitions returns exactly the three WAP sensors."""
    from phlo_dagster.wap_sensors import get_wap_definitions

    defs = get_wap_definitions()
    sensors = list(defs.sensors or [])
    sensor_names = {s.name for s in sensors}
    assert sensor_names == {
        "wap_branch_creation_sensor",
        "wap_auto_promotion_sensor",
        "wap_branch_cleanup_sensor",
    }


def test_wap_branch_creation_sensor_uses_updated_after_filter():
    """Branch creation sensor should scan by updated timestamp, not creation timestamp."""
    instance = MagicMock()
    instance.get_runs.return_value = []
    context = MagicMock()
    context.instance = instance
    context.cursor = None

    with patch("phlo_dagster.wap_sensors._load_versioned_catalog", return_value=MagicMock()):
        wap_branch_creation_sensor._raw_fn(context)

    filters = instance.get_runs.call_args.kwargs["filters"]
    assert filters.updated_after is not None
    assert filters.created_after is None
    context.update_cursor.assert_called_once()


def test_wap_auto_promotion_sensor_uses_updated_after_filter():
    """Promotion sensor should scan by updated timestamp, not creation timestamp."""
    instance = MagicMock()
    instance.get_runs.return_value = []
    context = MagicMock()
    context.instance = instance
    context.cursor = None

    with patch("phlo_dagster.wap_sensors._load_versioned_catalog", return_value=MagicMock()):
        wap_auto_promotion_sensor._raw_fn(context)

    filters = instance.get_runs.call_args.kwargs["filters"]
    assert filters.updated_after is not None
    assert filters.created_after is None
    context.update_cursor.assert_called_once()


def test_wap_successful_promotion_uses_recorded_check_event_identity(monkeypatch, tmp_path):
    """A passing Dagster check supplies the real quality evidence identity."""
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    run_id = "run-promote"
    branch = _wap_branch_name(run_id)
    write_wap_report(
        run_id,
        status="branch_created",
        branch=branch,
        project_id="project-promote",
        attempt=1,
    )

    check_record = SimpleNamespace(
        storage_id=42,
        event_log_entry=SimpleNamespace(
            asset_check_evaluation=SimpleNamespace(passed=True),
        ),
    )
    instance = MagicMock()
    instance.get_runs.return_value = [
        SimpleNamespace(
            run_id=run_id,
            tags={
                "phlo/wap_branch": branch,
                "phlo/project_id": "project-promote",
                "phlo/attempt": "1",
            },
        )
    ]
    instance.get_records_for_run.return_value = SimpleNamespace(records=[check_record])
    catalog = MagicMock()
    catalog.get_branch_hash.side_effect = ["source-before", "target-before", "target-after"]
    catalog.merge_branch.return_value = True
    catalog.delete_branch.return_value = True
    context = MagicMock()
    context.instance = instance
    context.cursor = None
    context.evaluation_time = datetime.now(timezone.utc)

    observations: list[dict[str, object]] = []
    monkeypatch.setattr(
        "phlo_dagster.wap_sensors.emit_observation",
        lambda **kwargs: observations.append(kwargs),
    )
    monkeypatch.setattr("phlo_dagster.wap_sensors._load_versioned_catalog", lambda: catalog)

    wap_auto_promotion_sensor._raw_fn(context)

    catalog.merge_branch.assert_called_once_with(source=branch, target="main")
    promotion = next(
        item for item in observations if item["catalog_change"]["operation"] == "promotion"
    )
    assert promotion["catalog_change"]["quality_decision_id"] == "dagster-quality:42"
    assert promotion["catalog_change"]["merge_outcome"] == "promoted"
