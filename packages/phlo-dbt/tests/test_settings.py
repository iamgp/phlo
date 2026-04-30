from __future__ import annotations

from phlo_dbt.settings import DbtSettings


def test_dbt_project_paths_resolve_from_phlo_project_path(monkeypatch, tmp_path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(project_root))

    settings = DbtSettings()

    assert settings.dbt_project_path == project_root / "workflows/transforms/dbt"
    assert settings.dbt_profiles_path == project_root / "workflows/transforms/dbt/profiles"
