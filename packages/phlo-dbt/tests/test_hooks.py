from __future__ import annotations

from phlo_dbt.hooks import _find_dagster_container


def test_find_dagster_container_uses_core_service_lookup(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake_find_service_container(**kwargs):
        captured.update(kwargs)
        return "demo-dagster-1"

    monkeypatch.setattr("phlo_dbt.hooks.find_service_container", _fake_find_service_container)

    assert _find_dagster_container("demo") == "demo-dagster-1"
    assert captured["project_name"] == "demo"
    assert captured["service_name"] == "dagster"
    assert captured["legacy_names"] == ("demo-dagster-webserver-1",)
    assert captured["exclude_substrings"] == ("daemon",)
