from phlo_lineage.cli_lineage import _resolve_asset_name
from phlo_lineage.cli_lineage import show_lineage
from phlo_lineage.graph import LineageGraph
from click.testing import CliRunner


def test_resolve_asset_name_maps_dlt_asset_to_raw_table_node() -> None:
    graph = LineageGraph()
    graph.add_asset("raw.orders")

    resolved_name, matches = _resolve_asset_name(graph, "dlt_orders")

    assert resolved_name == "raw.orders"
    assert matches == ["raw.orders"]


def test_resolve_asset_name_keeps_ambiguous_dlt_table_matches_unresolved() -> None:
    graph = LineageGraph()
    graph.add_asset("raw.orders")
    graph.add_asset("archive.orders")

    resolved_name, matches = _resolve_asset_name(graph, "dlt_orders")

    assert resolved_name is None
    assert sorted(matches) == ["archive.orders", "raw.orders"]


def test_show_lineage_renders_direction_labels(monkeypatch) -> None:
    graph = LineageGraph()
    graph.add_edge("raw.orders", "stg_orders")
    monkeypatch.setattr("phlo_lineage.cli_lineage.get_lineage_graph", lambda: graph)

    result = CliRunner().invoke(show_lineage, ["dlt_orders", "--direction", "both"])

    assert result.exit_code == 0
    assert "[downstream]" in result.output
