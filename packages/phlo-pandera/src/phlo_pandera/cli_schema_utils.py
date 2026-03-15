"""Shared CLI utilities for schema commands."""

import os
from pathlib import Path
from typing import Optional

from phlo.logging import get_logger
from rich.table import Table

logger = get_logger(__name__)


def _default_schema_search_paths() -> list[str]:
    """Return default schema search paths rooted at the project when available."""
    env_paths = os.getenv("PHLO_SCHEMA_SEARCH_PATHS")
    if env_paths:
        return [path.strip() for path in env_paths.split(",") if path.strip()]

    project_root = os.getenv("PHLO_PROJECT_PATH")
    if project_root:
        return [
            str(Path(project_root) / "examples"),
            str(Path(project_root) / "workflows"),
        ]

    return ["examples", "workflows"]


def format_table(title: str, columns: list[str], rows: list[tuple]) -> Table:
    """
    Create a Rich Table with given data.

    Args:
        title: Table title
        columns: List of column headers
        rows: List of tuples (one per row)

    Returns:
        Rich Table instance
    """
    table = Table(title=title)
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*[str(item) for item in row])
    return table


def discover_pandera_schemas(
    search_paths: Optional[list[str]] = None,
) -> dict[str, type]:
    """
    Discover all Pandera DataFrameModel subclasses.

    Scans specified directories for schema definitions and loads them.

    Args:
        search_paths: List of paths to search (default: examples/ and workflows/)
            or comma-separated PHLO_SCHEMA_SEARCH_PATHS environment variable.

    Returns:
        Dictionary mapping schema name to schema class
    """
    import inspect
    from importlib import import_module

    from pandera.pandas import DataFrameModel

    if search_paths is None:
        search_paths = _default_schema_search_paths()

    schemas = {}

    for search_path in search_paths:
        path = Path(search_path)
        if not path.exists():
            continue

        for py_file in path.glob("**/schemas/*.py"):
            if py_file.name.startswith("_"):
                continue

            try:
                parts = py_file.relative_to(path.parent).parts[:-1] + (py_file.stem,)
                module_name = ".".join(parts)

                try:
                    module = import_module(module_name)
                except (ImportError, ModuleNotFoundError):
                    logger.debug(
                        "schema_discovery_import_failed",
                        module_name=module_name,
                    )
                    continue

                for name, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, DataFrameModel)
                        and obj is not DataFrameModel
                    ):
                        schemas[name] = obj

            except Exception:
                logger.warning(
                    "schema_discovery_file_scan_failed",
                    search_path=str(path),
                    schema_file=str(py_file),
                )
                continue

    return schemas


def classify_schema_change(old_schema: dict, new_schema: dict) -> tuple[str, list[str]]:
    """
    Classify schema changes as SAFE, WARNING, or BREAKING.

    Args:
        old_schema: Original schema (dict of column_name -> type)
        new_schema: New schema (dict of column_name -> type)

    Returns:
        Tuple of (classification, details_list)
    """
    old_cols = set(old_schema.keys())
    new_cols = set(new_schema.keys())

    added = new_cols - old_cols
    removed = old_cols - new_cols
    changed = old_cols & new_cols

    details = []
    severity = "SAFE"

    if removed:
        details.append(f"Removed columns: {', '.join(removed)}")
        severity = "BREAKING"

    type_changes = []
    for col in changed:
        if old_schema[col] != new_schema[col]:
            type_changes.append(f"{col}: {old_schema[col]} -> {new_schema[col]}")

    if type_changes:
        details.append(f"Type changes: {', '.join(type_changes)}")
        severity = "BREAKING"

    if added:
        details.append(f"Added columns: {', '.join(added)}")
        if severity == "SAFE":
            severity = "SAFE"

    if not details:
        details.append("No changes detected")

    return severity, details
