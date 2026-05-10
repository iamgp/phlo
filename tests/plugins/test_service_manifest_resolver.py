from pathlib import Path

import pytest

from phlo.plugins.discovery._service_definition import ServiceDefinition
from phlo.plugins.discovery.service_manifest import (
    ServiceManifest,
    ServiceManifestError,
    ServiceManifestResolver,
)


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


def test_resolver_loads_service_yaml_files_from_directory(tmp_path: Path) -> None:
    service_dir = tmp_path / "services"
    service_dir.mkdir()
    (service_dir / "postgres.service.schema.yaml").write_text("name: ignored\n", encoding="utf-8")
    (service_dir / "postgres.yaml").write_text("name: ignored\nimage: busybox\n", encoding="utf-8")
    (service_dir / "service.yaml").write_text(
        "name: postgres\ndescription: Postgres\nimage: postgres:16\ndefault: true\n",
        encoding="utf-8",
    )

    resolver = ServiceManifestResolver(services_dir=service_dir)

    manifests = resolver.resolve_directory_manifests()

    assert [manifest.name for manifest in manifests] == ["postgres"]
    assert manifests[0].definition.image == "postgres:16"


def test_resolver_raises_contextual_error_for_bad_yaml(tmp_path: Path) -> None:
    service_dir = tmp_path / "services"
    service_dir.mkdir()
    bad_yaml = service_dir / "service.yaml"
    bad_yaml.write_text("name: [", encoding="utf-8")

    resolver = ServiceManifestResolver(services_dir=service_dir)

    with pytest.raises(ServiceManifestError) as exc:
        resolver.resolve_directory_manifests()

    assert "invalid service definition file" in str(exc.value)
    assert f"source={bad_yaml}" in str(exc.value)
