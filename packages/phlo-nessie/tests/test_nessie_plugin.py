"""Tests for Nessie service plugin."""

from phlo.capabilities import CapabilitySupport
from phlo_nessie.plugin import NessieServicePlugin
from phlo_nessie.resource import NessieResource
from phlo_nessie.resource_provider import NessieResourceProvider


def test_nessie_service_definition():
    """Validate Nessie service definition fields."""

    plugin = NessieServicePlugin()
    service_definition = plugin.service_definition

    assert service_definition["name"] == "nessie"
    assert service_definition["category"] == "core"


def test_nessie_service_builds_the_patched_stable_image() -> None:
    definition = NessieServicePlugin().service_definition

    assert definition["image"] == "phlo/nessie:0.108.3-netty4.2.16"
    assert definition["build"] == {"context": ".", "dockerfile": "nessie/Dockerfile"}
    assert "NESSIE_VERSION" not in definition["env_vars"]
    assert {
        "source": "libraries.sha256",
        "dest": "nessie/libraries.sha256",
    } in definition["files"]


def test_nessie_resource_provider_registers_catalog_capability() -> None:
    """Nessie should register as a versioned catalog capability."""
    provider = NessieResourceProvider()

    resources = provider.get_resources()
    catalogs = provider.get_catalogs()

    assert len(resources) == 1
    assert resources[0].name == "catalog_versioning"
    assert isinstance(resources[0].resource, NessieResource)

    assert len(catalogs) == 1
    assert catalogs[0].name == "nessie"
    assert isinstance(catalogs[0].provider, NessieResource)
    assert catalogs[0].support == CapabilitySupport(
        supports_refs=True,
        supports_promote=True,
    )
