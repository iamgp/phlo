"""Publishing configuration scaffolding.

Generates `publishing.yaml` entries from a dbt manifest.
"""

from __future__ import annotations

import fnmatch
import json
from pathlib import Path
from typing import Any, Iterable

import click
import yaml

from phlo.cli._services.utils import get_project_name
from phlo.config import get_settings


def _normalize_select_patterns(select: Iterable[str]) -> list[str]:
    patterns: list[str] = []
    for raw in select:
        for part in raw.split(","):
            part = part.strip()
            if part:
                patterns.append(part)
    return patterns


def _select_models(model_names: list[str], patterns: list[str]) -> list[str]:
    if not patterns:
        return model_names

    selected: list[str] = []
    for name in model_names:
        if any(fnmatch.fnmatchcase(name, pattern) for pattern in patterns):
            selected.append(name)
    return selected


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping at root in {path}")
    return data


def _dump_yaml(data: dict[str, Any]) -> str:
    return yaml.safe_dump(data, sort_keys=False)


def _load_manifest_models(manifest_path: Path) -> dict[str, dict[str, Any]]:
    try:
        manifest = json.loads(manifest_path.read_text())
    except OSError as e:
        raise click.ClickException(f"Failed to read manifest: {manifest_path} ({e})") from e
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Invalid JSON in manifest: {manifest_path} ({e})") from e

    models: dict[str, dict[str, Any]] = {}
    for unique_id, node in (manifest.get("nodes") or {}).items():
        if not isinstance(unique_id, str) or not unique_id.startswith("model."):
            continue
        if not isinstance(node, dict):
            continue
        name = node.get("name")
        if isinstance(name, str) and name:
            models[name] = node
    return models


def scaffold_publishing_config(
    *,
    existing_config: dict[str, Any],
    model_names: list[str],
    source_key: str,
    iceberg_schema: str,
    group: str,
    asset_name: str,
    description: str,
) -> dict[str, Any]:
    config: dict[str, Any] = dict(existing_config)
    publishing = config.get("publishing", {})
    if publishing is None:
        publishing = {}
    if not isinstance(publishing, dict):
        raise ValueError("Expected `publishing` to be a mapping in publishing.yaml")

    existing_entry = publishing.get(source_key, {}) or {}
    if not isinstance(existing_entry, dict):
        raise ValueError(f"Expected publishing.{source_key} to be a mapping in publishing.yaml")

    entry: dict[str, Any] = dict(existing_entry)
    entry.setdefault("name", asset_name)
    entry.setdefault("group", group)
    entry.setdefault("description", description)

    tables_existing = entry.get("tables", {}) or {}
    if not isinstance(tables_existing, dict):
        raise ValueError(f"Expected publishing.{source_key}.tables to be a mapping")

    tables: dict[str, str] = {str(k): str(v) for k, v in tables_existing.items()}
    for model_name in model_names:
        tables.setdefault(model_name, f"{iceberg_schema}.{model_name}")
    entry["tables"] = tables

    deps_existing = entry.get("dependencies", []) or []
    if not isinstance(deps_existing, list):
        raise ValueError(f"Expected publishing.{source_key}.dependencies to be a list")
    dependencies = [str(dep) for dep in deps_existing]
    for model_name in model_names:
        if model_name not in dependencies:
            dependencies.append(model_name)
    entry["dependencies"] = dependencies

    publishing[source_key] = entry
    config["publishing"] = publishing
    return config


@click.group()
def publishing():
    """Publishing configuration management commands."""


@publishing.command("scaffold")
@click.option(
    "--manifest",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Path to dbt manifest.json (default: from settings)",
)
@click.option(
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path("publishing.yaml"),
    show_default=True,
    help="Path to write publishing.yaml",
)
@click.option(
    "--select",
    "select_patterns",
    multiple=True,
    default=("mrt_*",),
    show_default=True,
    help="Model name glob(s) to include (comma-separated allowed)",
)
@click.option(
    "--source",
    "source_key",
    default=None,
    help="publishing.<source> key to write under (default: project name)",
)
@click.option(
    "--iceberg-schema",
    default="marts",
    show_default=True,
    help="Iceberg schema to reference in tables mapping",
)
@click.option(
    "--group",
    default="publishing",
    show_default=True,
    help="Dagster group_name for the publishing asset",
)
@click.option(
    "--asset-name",
    default=None,
    help="Dagster asset name to generate (default: publish_<source>_marts)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Print YAML to stdout instead of writing output file",
)
def scaffold_cmd(
    manifest: Path | None,
    output: Path,
    select_patterns: tuple[str, ...],
    source_key: str | None,
    iceberg_schema: str,
    group: str,
    asset_name: str | None,
    dry_run: bool,
):
    """Scaffold `publishing.yaml` from a dbt manifest.

    Idempotent: re-running preserves existing config and only adds missing tables/dependencies.
    """
    manifest_path = manifest or Path(get_settings().dbt_manifest_path)
    if not manifest_path.is_absolute():
        manifest_path = (Path.cwd() / manifest_path).resolve()
    if not manifest_path.exists():
        raise click.ClickException(f"dbt manifest not found at {manifest_path}")

    models = _load_manifest_models(manifest_path)
    all_model_names = sorted(models.keys())

    patterns = _normalize_select_patterns(select_patterns)
    selected_model_names = _select_models(all_model_names, patterns)
    if not selected_model_names:
        raise click.ClickException(f"No models matched selection: {', '.join(patterns)}")

    resolved_source_key = source_key or get_project_name()
    resolved_asset_name = asset_name or f"publish_{resolved_source_key}_marts"
    resolved_description = (
        f"Publish {len(selected_model_names)} dbt marts to Postgres via Trino (scaffolded)."
    )

    existing_config = _load_yaml(output)
    updated_config = scaffold_publishing_config(
        existing_config=existing_config,
        model_names=selected_model_names,
        source_key=resolved_source_key,
        iceberg_schema=iceberg_schema,
        group=group,
        asset_name=resolved_asset_name,
        description=resolved_description,
    )

    rendered = _dump_yaml(updated_config)
    if dry_run:
        click.echo(rendered)
        return

    output.write_text(rendered)
    click.echo(f"Wrote {output}")
