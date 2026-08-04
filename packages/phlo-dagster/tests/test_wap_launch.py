"""Tests for WAP launch coordination before Dagster starts a run."""

from __future__ import annotations

from types import SimpleNamespace

from phlo_dagster.wap_launch import WAP_BRANCH_TAG, WAP_REF_TAG, WAP_RUN_ID_TAG, prepare_wap_launch


class _Catalog:
    def __init__(self, branches: dict[str, str] | None = None) -> None:
        self.branches = branches or {"main": "main-hash"}
        self.created: list[tuple[str, str]] = []
        self.deleted: list[str] = []

    def get_branch_hash(self, name: str) -> str | None:
        return self.branches.get(name)

    def list_branches(self) -> list[object]:
        return []

    def create_branch(self, name: str, from_ref: str = "main") -> str:
        self.created.append((name, from_ref))
        self.branches[name] = "branch-hash"
        return "branch-hash"

    def delete_branch(self, name: str) -> bool:
        self.deleted.append(name)
        return self.branches.pop(name, None) is not None

    def merge_branch(self, source: str, target: str = "main") -> bool:
        return False


def test_prepare_wap_launch_creates_deterministic_branch_and_tags(monkeypatch) -> None:
    catalog = _Catalog()
    monkeypatch.setattr(
        "phlo_dagster.wap_launch.resolve_capability",
        lambda _: SimpleNamespace(
            provider=catalog,
            support=SimpleNamespace(supports_refs=True, supports_promote=True),
        ),
    )

    launch = prepare_wap_launch(logical_run_id="request-42")

    assert launch.branch == "pipeline-run-request-42"
    assert launch.created_branch is True
    assert launch.tags == {
        WAP_RUN_ID_TAG: "request-42",
        WAP_BRANCH_TAG: "pipeline-run-request-42",
        WAP_REF_TAG: "pipeline-run-request-42",
    }
    assert catalog.created == [("pipeline-run-request-42", "main")]


def test_prepare_wap_launch_reuses_existing_branch_for_retry(monkeypatch) -> None:
    catalog = _Catalog({"main": "main-hash", "pipeline-run-request-42": "old-hash"})
    monkeypatch.setattr(
        "phlo_dagster.wap_launch.resolve_capability",
        lambda _: SimpleNamespace(
            provider=catalog,
            support=SimpleNamespace(supports_refs=True, supports_promote=True),
        ),
    )

    launch = prepare_wap_launch(logical_run_id="request-42")
    launch.cleanup_if_created()

    assert launch.created_branch is False
    assert catalog.created == []
    assert catalog.deleted == []
