"""Canonical dbt runtime configuration derived from Phlo settings."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from phlo.capabilities import (
    CapabilitySupport,
    RuntimeContext,
    resolve_runtime_ref,
    routing_from_context,
)
from phlo_trino.settings import get_settings as get_trino_settings
import yaml

DEFAULT_DBT_TARGET = "dev"
DBT_QUERY_ENGINE_SUPPORT = CapabilitySupport(supports_refs=True)


@dataclass(frozen=True, slots=True)
class DbtRuntimeConfig:
    """Canonical dbt runtime configuration for the active execution target."""

    profile_name: str = "phlo"
    target_name: str = DEFAULT_DBT_TARGET
    user: str = "dagster"
    host: str = "trino"
    port: int = 8080
    catalog: str = "iceberg"
    schema: str = "raw"
    threads: int = 2
    http_scheme: str = "http"
    method: str = "none"

    def to_profile_payload(self) -> dict[str, Any]:
        """Return the config in dbt `profiles.yml` shape."""
        return {
            self.profile_name: {
                "target": self.target_name,
                "outputs": {
                    self.target_name: {
                        "type": "trino",
                        "method": self.method,
                        "user": self.user,
                        "host": self.host,
                        "port": self.port,
                        "catalog": self.catalog,
                        "schema": self.schema,
                        "http_scheme": self.http_scheme,
                        "threads": self.threads,
                    }
                },
            }
        }


def resolve_dbt_target_name(
    runtime: RuntimeContext | None = None, *, target: str | None = None
) -> str:
    """Resolve the effective dbt target name from canonical routing.

    Resolution order:
    1. Explicit target argument
    2. Canonical routing environment
    3. Legacy `dbt_target` tag
    4. Default `DEFAULT_DBT_TARGET`
    """
    if target:
        return target
    if runtime is not None:
        routing = routing_from_context(runtime)
        if routing.environment:
            return routing.environment
        runtime_tags = getattr(runtime, "tags", {}) or {}
        legacy_target = runtime_tags.get("dbt_target") if isinstance(runtime_tags, dict) else None
        if isinstance(legacy_target, str) and legacy_target:
            return legacy_target
    return DEFAULT_DBT_TARGET


def resolve_dbt_runtime_config(
    runtime: RuntimeContext | None = None,
    *,
    target: str | None = None,
) -> DbtRuntimeConfig:
    """Resolve canonical dbt runtime config from query-engine settings and routing."""
    trino = get_trino_settings()
    target_name = resolve_dbt_target_name(runtime, target=target)
    catalog = trino.trino_catalog
    ref = resolve_runtime_ref(runtime, support=DBT_QUERY_ENGINE_SUPPORT, default_ref="main")
    if ref and ref != "main":
        catalog = f"{catalog}_{ref}"

    return DbtRuntimeConfig(
        target_name=target_name,
        host=trino.trino_host,
        port=trino.trino_port,
        catalog=catalog,
    )


def render_dbt_profile_yaml(config: DbtRuntimeConfig) -> str:
    """Render canonical dbt runtime config as `profiles.yml` text."""
    return yaml.safe_dump(config.to_profile_payload(), sort_keys=False)


def write_dbt_profile(
    config: DbtRuntimeConfig,
    profiles_dir: Path,
    *,
    filename: str = "profiles.yml",
) -> Path:
    """Write canonical `profiles.yml` to disk and return its path."""
    profiles_dir.mkdir(parents=True, exist_ok=True)
    profile_path = profiles_dir / filename
    profile_path.write_text(render_dbt_profile_yaml(config), encoding="utf-8")
    return profile_path


def ensure_dbt_profile(
    profiles_dir: Path,
    *,
    runtime: RuntimeContext | None = None,
    target: str | None = None,
) -> Path:
    """Resolve and write canonical `profiles.yml` for the active dbt target."""
    return write_dbt_profile(
        resolve_dbt_runtime_config(runtime, target=target),
        profiles_dir,
    )
