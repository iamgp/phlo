from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from pathlib import PurePosixPath
from typing import Any

from dagster import AssetKey
from dagster_dbt import DagsterDbtTranslator

from phlo.config import config


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _first_matching_layer(segments: Sequence[str]) -> str | None:
    layer_map = {
        "bronze": "bronze",
        "silver": "silver",
        "gold": "gold",
        "marts": "marts",
        "mart": "marts",
        "staging": "silver",
        "stage": "silver",
        "stg": "silver",
    }

    for segment in segments:
        layer = layer_map.get(segment)
        if layer is not None:
            return layer
    return None


def _path_segments_from_props(dbt_resource_props: Mapping[str, Any]) -> list[str]:
    path = str(dbt_resource_props.get("path") or dbt_resource_props.get("original_file_path") or "")
    if not path:
        return []

    normalized = path.replace("\\", "/")
    return [segment for segment in PurePosixPath(normalized).parts if segment not in {".", ""}]


def _fqn_segments_from_props(dbt_resource_props: Mapping[str, Any]) -> list[str]:
    fqn = dbt_resource_props.get("fqn")
    if not isinstance(fqn, list):
        return []
    return [str(segment) for segment in fqn]


def _truncate_utf8_bytes(text: str, max_bytes: int) -> tuple[str, bool, int]:
    raw = text.encode("utf-8")
    if len(raw) <= max_bytes:
        return text, False, len(raw)

    truncated = raw[:max_bytes].decode("utf-8", errors="ignore")
    return truncated, True, len(raw)


def get_compiled_sql_from_resource_props(
    dbt_resource_props: Mapping[str, Any], *, max_bytes: int
) -> tuple[str, bool, int, str]:
    compiled_sql = ""
    source = "none"

    compiled_path = dbt_resource_props.get("compiled_path")
    if compiled_path:
        compiled_file = config.dbt_project_path / str(compiled_path)
        try:
            if compiled_file.exists():
                compiled_sql = compiled_file.read_text()
                source = "compiled_file"
        except OSError:
            pass

    if not compiled_sql:
        compiled_sql = str(
            dbt_resource_props.get("compiled_code")
            or dbt_resource_props.get("raw_code")
            or dbt_resource_props.get("raw_sql")
            or ""
        )
        if compiled_sql:
            source = "manifest"

    if not compiled_sql:
        return "", False, 0, source

    truncated_sql, was_truncated, original_bytes = _truncate_utf8_bytes(compiled_sql, max_bytes)
    if was_truncated:
        marker = (
            f"\n\n-- [phlo] TRUNCATED compiled SQL: {original_bytes} bytes "
            f"(limit {max_bytes} bytes)"
        )
        truncated_sql = f"{truncated_sql}{marker}"

    return truncated_sql, was_truncated, original_bytes, source


class CustomDbtTranslator(DagsterDbtTranslator):
    """Custom translator for mapping dbt models to Dagster assets."""

    def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> AssetKey:
        resource_type = dbt_resource_props.get("resource_type")
        is_source = resource_type == "source" or (
            resource_type is None and "source_name" in dbt_resource_props
        )

        if is_source:
            source_name = dbt_resource_props["source_name"]
            table_name = dbt_resource_props["name"]
            if source_name == "dagster_assets":
                return AssetKey([f"dlt_{table_name}"])
            return super().get_asset_key(dbt_resource_props)

        return AssetKey(str(dbt_resource_props["name"]))

    def get_description(self, dbt_resource_props: Mapping[str, Any]) -> str:
        model_name = str(dbt_resource_props.get("name", ""))
        docstring = str(dbt_resource_props.get("description") or "")

        parts = [f"dbt model {model_name}"]
        if docstring:
            parts.append(docstring)

        if _bool_env("PHLO_DBT_INCLUDE_COMPILED_SQL_IN_DESCRIPTION", default=False):
            max_bytes = _int_env("PHLO_DBT_COMPILED_SQL_MAX_BYTES", default=64_000)
            compiled_sql, _, _, _ = get_compiled_sql_from_resource_props(
                dbt_resource_props, max_bytes=max_bytes
            )
            if compiled_sql:
                parts.append("\n#### Compiled SQL (truncated):\n```sql\n" + compiled_sql + "\n```")

        return "\n\n".join(parts)

    def get_group_name(self, dbt_resource_props: Mapping[str, Any]) -> str:
        meta = dbt_resource_props.get("meta", {})
        if isinstance(meta, dict) and "group" in meta:
            return str(meta["group"])

        path_layer = _first_matching_layer(_path_segments_from_props(dbt_resource_props))
        if path_layer is not None:
            return path_layer

        fqn_layer = _first_matching_layer(_fqn_segments_from_props(dbt_resource_props))
        if fqn_layer is not None:
            return fqn_layer

        model_name = str(dbt_resource_props.get("name", ""))
        if model_name.startswith("stg_"):
            return "silver"
        if model_name.startswith(("dim_", "fct_")):
            return "gold"
        if model_name.startswith("mrt_"):
            return "marts"
        return "transform"

    def get_metadata(self, dbt_resource_props: Mapping[str, Any]) -> dict[str, Any]:
        metadata: dict[str, Any] = dict(super().get_metadata(dbt_resource_props) or {})

        columns = dbt_resource_props.get("columns", {})
        if isinstance(columns, dict) and columns:
            from dagster import TableColumn, TableSchema

            table_columns = [
                TableColumn(
                    name=str(col_name),
                    type=str(col_info.get("data_type", "unknown")),
                    description=str(col_info.get("description", "")),
                )
                for col_name, col_info in columns.items()
                if isinstance(col_info, dict)
            ]
            if table_columns:
                metadata.setdefault("dagster/column_schema", TableSchema(columns=table_columns))

        max_bytes = _int_env("PHLO_DBT_COMPILED_SQL_MAX_BYTES", default=64_000)
        compiled_sql, was_truncated, original_bytes, source = get_compiled_sql_from_resource_props(
            dbt_resource_props, max_bytes=max_bytes
        )
        if compiled_sql:
            metadata["phlo/compiled_sql"] = compiled_sql
            metadata["phlo/compiled_sql_truncated"] = was_truncated
            metadata["phlo/compiled_sql_bytes"] = original_bytes
            metadata["phlo/compiled_sql_byte_limit"] = max_bytes
            metadata["phlo/compiled_sql_source"] = source

        return metadata

    def get_kinds(self, dbt_resource_props: Mapping[str, Any]) -> set[str]:
        return {"dbt", "trino"}
