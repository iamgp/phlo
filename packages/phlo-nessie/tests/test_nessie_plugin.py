"""Tests for Nessie service plugin."""

from phlo_nessie.plugin import NessieServicePlugin


def test_nessie_service_definition():
    """Validate Nessie service definition fields."""

    plugin = NessieServicePlugin()
    service_definition = plugin.service_definition

    assert service_definition["name"] == "nessie"
    assert service_definition["category"] == "core"
