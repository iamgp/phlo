from __future__ import annotations

import yaml
from types import SimpleNamespace

from phlo_dbt.runtime_config import (
    DbtRuntimeConfig,
    render_dbt_profile_yaml,
    resolve_dbt_runtime_config,
    resolve_dbt_target_name,
    write_dbt_profile,
)


def test_dbt_runtime_config_to_profile_payload() -> None:
    config = DbtRuntimeConfig(
        target_name="ci",
        host="trino-ci",
        port=8090,
        catalog="iceberg_dev",
    )

    assert config.to_profile_payload() == {
        "phlo": {
            "target": "ci",
            "outputs": {
                "ci": {
                    "type": "trino",
                    "method": "none",
                    "user": "dagster",
                    "host": "trino-ci",
                    "port": 8090,
                    "catalog": "iceberg_dev",
                    "schema": "raw",
                    "http_scheme": "http",
                    "threads": 2,
                }
            },
        }
    }


def test_resolve_dbt_target_name_prefers_explicit_target() -> None:
    runtime = SimpleNamespace(tags={"environment": "ci"})

    assert resolve_dbt_target_name(runtime, target="prod") == "prod"


def test_resolve_dbt_target_name_prefers_environment() -> None:
    runtime = SimpleNamespace(
        run_id="run-1",
        partition_key=None,
        tags={"environment": "ci", "dbt_target": "legacy"},
        resources={},
    )

    assert resolve_dbt_target_name(runtime) == "ci"


def test_resolve_dbt_target_name_falls_back_to_legacy_tag() -> None:
    runtime = SimpleNamespace(
        run_id="run-1",
        partition_key=None,
        tags={"dbt_target": "qa"},
        resources={},
    )

    assert resolve_dbt_target_name(runtime) == "qa"


def test_resolve_dbt_runtime_config_uses_ref_aware_catalog() -> None:
    runtime = SimpleNamespace(
        run_id="run-1",
        partition_key=None,
        tags={"environment": "dev", "phlo/ref": "feature_orders"},
        resources={},
    )

    config = resolve_dbt_runtime_config(runtime)

    assert config.target_name == "dev"
    assert config.catalog == "iceberg_feature_orders"


def test_resolve_dbt_runtime_config_defaults_to_main_catalog() -> None:
    config = resolve_dbt_runtime_config()

    assert config.target_name == "dev"
    assert config.catalog == "iceberg"


def test_render_dbt_profile_yaml_returns_expected_yaml() -> None:
    config = DbtRuntimeConfig(target_name="ci", catalog="iceberg_feature_orders")

    payload = yaml.safe_load(render_dbt_profile_yaml(config))

    assert payload["phlo"]["target"] == "ci"
    assert payload["phlo"]["outputs"]["ci"]["catalog"] == "iceberg_feature_orders"


def test_write_dbt_profile_writes_profiles_file(tmp_path) -> None:
    config = DbtRuntimeConfig(target_name="dev")

    profile_path = write_dbt_profile(config, tmp_path / "profiles")

    assert profile_path.name == "profiles.yml"
    assert profile_path.exists()
    payload = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    assert payload["phlo"]["outputs"]["dev"]["host"] == "trino"
