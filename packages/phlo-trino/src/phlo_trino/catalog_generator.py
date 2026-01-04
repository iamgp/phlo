"""Trino catalog generator from discovered plugins."""

from __future__ import annotations

import os
import importlib.metadata
from pathlib import Path

from phlo.discovery.plugins import discover_plugins
from phlo.logging import get_logger, setup_logging
from phlo.plugins.base import CatalogPlugin

logger = get_logger(__name__)


def _load_entry_points(group: str) -> list[CatalogPlugin]:
    try:
        entry_points = importlib.metadata.entry_points(group=group)
    except TypeError:
        all_entry_points = importlib.metadata.entry_points()
        entry_points = all_entry_points.get(group, [])

    catalogs: list[CatalogPlugin] = []
    for entry_point in entry_points:
        try:
            plugin_class = entry_point.load()
            plugin = plugin_class() if isinstance(plugin_class, type) else plugin_class
            if isinstance(plugin, CatalogPlugin):
                catalogs.append(plugin)
            else:
                logger.error(
                    "Catalog plugin %s does not inherit from CatalogPlugin",
                    entry_point.name,
                )
        except Exception as exc:
            logger.error("Failed to instantiate catalog plugin %s: %s", entry_point.name, exc)

    return catalogs


def _filter_catalogs(catalogs: list[CatalogPlugin], target: str) -> list[CatalogPlugin]:
    filtered: list[CatalogPlugin] = []
    for catalog in catalogs:
        if catalog.supports_target(target):
            filtered.append(catalog)
            logger.info("Discovered %s catalog: %s", target, catalog.catalog_name)
        else:
            logger.debug(
                "Skipping catalog %s (targets=%s) for target=%s",
                catalog.catalog_name,
                catalog.targets,
                target,
            )
    return filtered


def discover_trino_catalogs() -> list[CatalogPlugin]:
    """Discover Trino-compatible catalog plugins via entry points."""
    plugins = discover_plugins(plugin_type="catalogs", auto_register=False)
    catalogs: list[CatalogPlugin] = []
    for plugin in plugins.get("catalogs", []):
        if isinstance(plugin, CatalogPlugin):
            catalogs.append(plugin)

    legacy_catalogs = _load_entry_points("phlo.plugins.trino_catalogs")
    if legacy_catalogs:
        logger.warning(
            "Detected legacy phlo.plugins.trino_catalogs entry points. "
            "Please migrate to phlo.plugins.catalogs."
        )

    combined = catalogs + legacy_catalogs
    unique: dict[str, CatalogPlugin] = {}
    for catalog in combined:
        if catalog.catalog_name not in unique:
            unique[catalog.catalog_name] = catalog

    return _filter_catalogs(list(unique.values()), "trino")


def _to_properties_file(properties: dict[str, object]) -> str:
    lines = [f"{key}={value}" for key, value in properties.items()]
    return "\n".join(lines) + "\n"


def generate_catalog_files(output_dir: str | Path | None = None) -> dict[str, Path]:
    """
    Generate Trino catalog .properties files from discovered plugins.

    Args:
        output_dir: Directory to write catalog files. Defaults to ./trino/catalog/

    Returns:
        Dictionary mapping catalog name to generated file path
    """
    if output_dir is None:
        output_dir = Path(os.environ.get("TRINO_CATALOG_DIR", "./trino/catalog"))
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    catalogs = discover_trino_catalogs()
    generated = {}

    for catalog in catalogs:
        try:
            filename = f"{catalog.catalog_name}.properties"
            filepath = output_dir / filename
            content = _to_properties_file(catalog.get_properties())

            filepath.write_text(content)
            generated[catalog.catalog_name] = filepath
            logger.info("Generated catalog file: %s", filepath)
        except Exception as exc:
            logger.error("Failed to generate catalog %s: %s", catalog.catalog_name, exc)

    return generated


if __name__ == "__main__":
    import sys

    setup_logging()

    output = sys.argv[1] if len(sys.argv) > 1 else None
    result = generate_catalog_files(output)
    logger.info("Generated %s catalog files:", len(result))
    for name, path in result.items():
        logger.info("  - %s: %s", name, path)
