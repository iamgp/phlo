"""Trino catalog generator from discovered plugins."""

from __future__ import annotations

import os
from pathlib import Path

from phlo.discovery.plugins import discover_plugins
from phlo.logging import get_logger, setup_logging
from phlo.plugins.base import TrinoCatalogPlugin

logger = get_logger(__name__)


def discover_trino_catalogs() -> list[TrinoCatalogPlugin]:
    """Discover all Trino catalog plugins via entry points."""
    plugins = discover_plugins(plugin_type="trino_catalogs", auto_register=False)
    catalogs = []

    for name, plugin_entries in plugins.items():
        try:
            for entry in plugin_entries:
                plugin = entry() if isinstance(entry, type) else entry
                if isinstance(plugin, TrinoCatalogPlugin):
                    catalogs.append(plugin)
                    logger.info("Discovered Trino catalog: %s", plugin.catalog_name)
        except Exception as exc:
            logger.error("Failed to instantiate catalog plugin %s: %s", name, exc)

    return catalogs


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
            content = catalog.to_properties_file()

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
