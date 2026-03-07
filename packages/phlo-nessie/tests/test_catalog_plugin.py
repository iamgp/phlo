"""Tests for Nessie-owned catalog plugins."""

from phlo_nessie.catalog_plugin import (
    NessieIcebergCatalogPlugin,
    NessieIcebergDevCatalogPlugin,
)


def test_nessie_catalog_plugin_exposes_main_catalog_properties(monkeypatch) -> None:
    """Main catalog plugin should emit Nessie-backed Trino properties."""
    monkeypatch.setattr(
        "phlo_nessie.catalog_plugin.get_settings",
        lambda: type(
            "Settings", (), {"nessie_iceberg_rest_uri": lambda self: "http://nessie:19120/iceberg"}
        )(),
    )
    plugin = NessieIcebergCatalogPlugin()

    props = plugin.get_properties()

    assert plugin.catalog_name == "iceberg"
    assert props["iceberg.rest-catalog.uri"] == "http://nessie:19120/iceberg"
    assert "iceberg.rest-catalog.prefix" not in props


def test_nessie_catalog_plugin_exposes_dev_catalog_prefix(monkeypatch) -> None:
    """Dev catalog plugin should pin the Trino prefix to the dev ref."""
    monkeypatch.setattr(
        "phlo_nessie.catalog_plugin.get_settings",
        lambda: type(
            "Settings", (), {"nessie_iceberg_rest_uri": lambda self: "http://nessie:19120/iceberg"}
        )(),
    )
    plugin = NessieIcebergDevCatalogPlugin()

    props = plugin.get_properties()

    assert plugin.catalog_name == "iceberg_dev"
    assert props["iceberg.rest-catalog.prefix"] == "dev"
