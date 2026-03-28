"""Tests for dbt manifest lineage import helpers."""

from __future__ import annotations

import json
from types import SimpleNamespace

from phlo_lineage.store import ColumnLineage

from phlo_dbt.lineage_import import collect_asset_lineage, import_manifest_lineage


def test_collect_asset_lineage_returns_edges_and_targets() -> None:
    manifest = {
        "nodes": {
            "model.demo.dim_pokemon": {
                "resource_type": "model",
                "schema": "gold",
                "name": "dim_pokemon",
                "depends_on": {"nodes": ["model.demo.stg_pokemon", "source.demo.raw_pokemon"]},
            },
            "model.demo.stg_pokemon": {
                "resource_type": "model",
                "schema": "silver",
                "name": "stg_pokemon",
                "depends_on": {"nodes": ["source.demo.raw_pokemon"]},
            },
        },
        "sources": {
            "source.demo.raw_pokemon": {
                "resource_type": "source",
                "source_name": "raw",
                "name": "pokemon",
            }
        },
    }

    edges, asset_keys = collect_asset_lineage(manifest)

    assert edges == [
        ("stg_pokemon", "dim_pokemon"),
        ("raw.pokemon", "dim_pokemon"),
        ("raw.pokemon", "stg_pokemon"),
    ]
    assert asset_keys == ["dim_pokemon", "stg_pokemon"]


def test_import_manifest_lineage_persists_assets_and_columns(monkeypatch, tmp_path) -> None:
    manifest_path = tmp_path / "target" / "manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest = {
        "nodes": {
            "model.demo.dim_pokemon": {
                "resource_type": "model",
                "schema": "gold",
                "name": "dim_pokemon",
                "depends_on": {"nodes": ["model.demo.stg_pokemon"]},
                "columns": {"id": {}, "name": {}},
            },
            "model.demo.stg_pokemon": {
                "resource_type": "model",
                "schema": "silver",
                "name": "stg_pokemon",
                "depends_on": {"nodes": []},
                "columns": {"id": {}, "name": {}, "type": {}},
            },
        },
        "sources": {},
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    sink = SimpleNamespace()
    sink_calls: list[tuple[list[tuple[str, str]], list[str] | None, dict[str, object] | None]] = []
    sink.record_asset_edges = (
        lambda edges, *, asset_keys=None, metadata=None, tags=None: sink_calls.append(
            (edges, asset_keys, metadata)
        )
        or len(edges)
    )
    monkeypatch.setattr("phlo_dbt.lineage_import.discover_capabilities", lambda: None)
    monkeypatch.setattr(
        "phlo_dbt.lineage_import.resolve_capability",
        lambda capability_type: SimpleNamespace(name="phlo-lineage", provider=sink)
        if capability_type == "lineage_sink"
        else None,
    )

    recorded_mappings: list[list[ColumnLineage]] = []
    monkeypatch.setattr(
        "phlo_lineage.dbt_column_lineage.extract_column_lineage",
        lambda payload: [
            ColumnLineage(
                source_asset="silver.stg_pokemon",
                source_column="id",
                target_asset="gold.dim_pokemon",
                target_column="id",
                source_type="dbt_heuristic",
            )
        ],
    )
    monkeypatch.setattr(
        "phlo_lineage.store.resolve_lineage_db_url_with_postgres_fallback",
        lambda: "postgresql://lineage",
    )

    class _Store:
        def __init__(self, connection_string: str) -> None:
            assert connection_string == "postgresql://lineage"

        def record_column_lineage(self, mappings: list[ColumnLineage]) -> int:
            recorded_mappings.append(mappings)
            return len(mappings)

    monkeypatch.setattr("phlo_lineage.store.LineageStore", _Store)

    summary = import_manifest_lineage(manifest_path)

    assert summary == {"asset_edges": 1, "column_mappings": 1}
    assert sink_calls == [
        (
            [("stg_pokemon", "dim_pokemon")],
            ["dim_pokemon", "stg_pokemon"],
            {"source": "dbt", "manifest_path": str(manifest_path)},
        )
    ]
    assert len(recorded_mappings) == 1


def test_import_manifest_lineage_skips_when_no_sink(monkeypatch, tmp_path) -> None:
    manifest_path = tmp_path / "target" / "manifest.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(json.dumps({"nodes": {}, "sources": {}}), encoding="utf-8")

    monkeypatch.setattr("phlo_dbt.lineage_import.discover_capabilities", lambda: None)
    monkeypatch.setattr(
        "phlo_dbt.lineage_import.resolve_capability",
        lambda capability_type: None,
    )

    assert import_manifest_lineage(manifest_path) == {"asset_edges": 0, "column_mappings": 0}
