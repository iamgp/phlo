"""Tests for Nessie service plugin."""

from phlo_nessie.plugin import NessieServicePlugin


def test_nessie_service_definition():
    plugin = NessieServicePlugin()
    service_definition = plugin.service_definition

    assert service_definition["name"] == "nessie"
    assert service_definition["category"] == "core"
