"""Tests for Trino service plugin."""

from phlo_trino.plugin import TrinoServicePlugin


def test_trino_service_definition():
    plugin = TrinoServicePlugin()
    service_definition = plugin.service_definition

    assert service_definition["name"] == "trino"
    assert service_definition["category"] == "core"
