"""Tests for WAP (Write-Audit-Publish) lifecycle sensors."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from phlo_dagster.wap_sensors import (
    _all_checks_passed,
    _wap_branch_name,
    wap_auto_promotion_sensor,
    wap_branch_creation_sensor,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def test_wap_branch_name():
    assert _wap_branch_name("abc123") == "pipeline/run-abc123"


# ---------------------------------------------------------------------------
# _all_checks_passed
# ---------------------------------------------------------------------------


class _FakeCheckEvaluation:
    def __init__(self, passed: bool):
        self.passed = passed


class _FakeEvent:
    def __init__(self, passed: bool):
        self.event_type = "ASSET_CHECK_EVALUATION"
        self.asset_check_evaluation = _FakeCheckEvaluation(passed)


def test_all_checks_passed_no_events():
    """No check events means nothing failed — returns True."""
    instance = MagicMock()
    instance.get_event_log_entries.return_value = []
    assert _all_checks_passed(instance, "run-1") is True


def test_all_checks_passed_all_pass():
    """All checks passing returns True."""
    instance = MagicMock()
    instance.get_event_log_entries.return_value = [
        _FakeEvent(passed=True),
        _FakeEvent(passed=True),
    ]
    assert _all_checks_passed(instance, "run-1") is True


def test_all_checks_passed_one_fails():
    """A single failing check returns False."""
    instance = MagicMock()
    instance.get_event_log_entries.return_value = [
        _FakeEvent(passed=True),
        _FakeEvent(passed=False),
    ]
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

        result = nessie.create_branch("pipeline/run-1", from_ref="main")
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

        result = nessie.create_branch("pipeline/run-1", from_ref="nonexistent")
        assert result is None

    @patch("phlo_nessie.resource.requests")
    def test_merge_branch_success(self, mock_requests):
        """merge_branch returns True on success."""
        nessie = self._make_resource()

        mock_get = MagicMock()
        mock_get.status_code = 200
        mock_get.json.return_value = {"hash": "abc123"}

        mock_post = MagicMock()
        mock_post.status_code = 200

        mock_requests.get.return_value = mock_get
        mock_requests.post.return_value = mock_post

        result = nessie.merge_branch(source="pipeline/run-1", target="main")
        assert result is True

    @patch("phlo_nessie.resource.requests")
    def test_merge_branch_conflict(self, mock_requests):
        """merge_branch returns False on conflict."""
        nessie = self._make_resource()

        mock_get = MagicMock()
        mock_get.status_code = 200
        mock_get.json.return_value = {"hash": "abc123"}

        mock_post = MagicMock()
        mock_post.status_code = 409

        mock_requests.get.return_value = mock_get
        mock_requests.post.return_value = mock_post

        result = nessie.merge_branch(source="pipeline/run-1", target="main")
        assert result is False


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

    with patch("phlo_dagster.wap_sensors._load_nessie", return_value=lambda: MagicMock()):
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

    with patch("phlo_dagster.wap_sensors._load_nessie", return_value=lambda: MagicMock()):
        wap_auto_promotion_sensor._raw_fn(context)

    filters = instance.get_runs.call_args.kwargs["filters"]
    assert filters.updated_after is not None
    assert filters.created_after is None
    context.update_cursor.assert_called_once()
