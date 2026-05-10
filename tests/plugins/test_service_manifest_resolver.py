from pathlib import Path

import pytest

from phlo.plugins.discovery._service_definition import ServiceDefinition
from phlo.plugins.discovery.service_manifest import ServiceManifest, ServiceManifestError


def test_service_manifest_wraps_definition_and_source_path(tmp_path: Path) -> None:
    definition = ServiceDefinition.from_dict(
        {
            "name": "postgres",
            "image": "postgres:16",
            "default": True,
            "depends_on": [],
        },
        tmp_path / "service.yaml",
    )

    manifest = ServiceManifest(definition=definition, source_path=tmp_path / "service.yaml")

    assert manifest.name == "postgres"
    assert manifest.definition is definition
    assert manifest.source_path == tmp_path / "service.yaml"


def test_service_manifest_error_includes_context() -> None:
    error = ServiceManifestError(
        "invalid service definition",
        service_name="postgres",
        source_path=Path("services/postgres/service.yaml"),
    )

    assert str(error) == "invalid service definition: service=postgres source=services/postgres/service.yaml"
