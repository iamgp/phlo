"""Tests for provider-neutral Iceberg mutation evidence semantics."""

from phlo_iceberg import evidence


def test_successful_mutation_with_absent_readback_keeps_provider_success(monkeypatch) -> None:
    captured: list[dict[str, object]] = []
    monkeypatch.setattr(
        evidence,
        "emit_observation",
        lambda **kwargs: captured.append(kwargs),
    )

    evidence.emit_mutation(
        context={"project_id": "project", "run_id": "run", "attempt": 2},
        table_name="raw.events",
        ref="main",
        operation="append",
        status="success",
        before={"state": "present", "snapshot_id": "before"},
        after={"state": "absent", "snapshot_id": None},
    )

    assert captured[0]["status"] == "success"
    assert captured[0]["resources"][0]["metadata"]["outcome"] == "contradictory"
    assert captured[0]["resources"][0]["metadata"]["evidence_completeness"] == "incomplete"


def test_mutation_evidence_sink_failure_is_contained(monkeypatch) -> None:
    def fail(**_kwargs):
        raise TypeError("evidence sink failed")

    monkeypatch.setattr(evidence, "emit_observation", fail)

    evidence.emit_mutation(
        context={"project_id": "project", "run_id": "run", "attempt": 1},
        table_name="raw.events",
        ref="main",
        operation="append",
        status="success",
        before={"state": "present"},
        after={"state": "unavailable"},
    )
