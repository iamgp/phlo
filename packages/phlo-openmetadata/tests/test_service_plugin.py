"""OpenMetadata generated service contracts."""

from importlib import resources

import yaml

from phlo_openmetadata.plugin import OpenMetadataServicePlugin


def test_openmetadata_builds_a_patched_stable_server_image() -> None:
    definition = OpenMetadataServicePlugin().service_definition
    dockerfile = resources.files("phlo_openmetadata").joinpath("Dockerfile").read_text()

    assert definition["image"] == "ghcr.io/phlohouse/phlo-openmetadata:1.13.1-java-patches"
    assert definition["build"] == {
        "context": ".",
        "dockerfile": "openmetadata/Dockerfile",
    }
    assert "FROM docker.io/openmetadata/server:1.13.1@sha256:eaa3185" in dockerfile
    assert "docker.getcollate.io" not in dockerfile
    assert "OPENMETADATA_VERSION" not in definition["env_vars"]


def test_openmetadata_mysql_builds_the_updated_stable_database_image() -> None:
    raw = resources.files("phlo_openmetadata").joinpath("openmetadata-mysql-setup.yaml").read_text()
    definition = yaml.safe_load(raw)
    dockerfile = resources.files("phlo_openmetadata").joinpath("db.Dockerfile").read_text()

    assert definition["image"] == "ghcr.io/phlohouse/phlo-openmetadata-db:1.13.1-ol8.10"
    assert definition["build"] == {
        "context": ".",
        "dockerfile": "openmetadata-mysql/Dockerfile",
    }
    assert "FROM docker.io/openmetadata/db:1.13.1@sha256:6659446" in dockerfile
    assert "docker.getcollate.io" not in dockerfile


def test_openmetadata_setup_uses_the_patched_server_image() -> None:
    raw = resources.files("phlo_openmetadata").joinpath("openmetadata-setup.yaml").read_text()
    definition = yaml.safe_load(raw)

    assert definition["image"] == "ghcr.io/phlohouse/phlo-openmetadata:1.13.1-java-patches"
    assert definition["build"] == {
        "context": ".",
        "dockerfile": "openmetadata/Dockerfile",
    }


def test_openmetadata_elasticsearch_builds_the_patched_compatible_image() -> None:
    raw = (
        resources.files("phlo_openmetadata")
        .joinpath("openmetadata-elasticsearch-setup.yaml")
        .read_text()
    )
    definition = yaml.safe_load(raw)

    assert definition["image"] == (
        "ghcr.io/phlohouse/phlo-openmetadata-elasticsearch:8.11.4-java-patches"
    )
    assert definition["build"] == {
        "context": ".",
        "dockerfile": "openmetadata-elasticsearch/Dockerfile",
    }
    assert {
        "source": "es-libraries.sha256",
        "dest": "openmetadata-elasticsearch/libraries.sha256",
    } in definition["files"]

    dockerfile = resources.files("phlo_openmetadata").joinpath("es.Dockerfile").read_text()
    assert "COPY openmetadata-elasticsearch/libraries.sha256 libraries.sha256" in dockerfile
