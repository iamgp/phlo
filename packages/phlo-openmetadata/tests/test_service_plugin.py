"""OpenMetadata generated service contracts."""

from importlib import resources

import yaml

from phlo_openmetadata.plugin import OpenMetadataServicePlugin


def test_openmetadata_builds_a_patched_stable_server_image() -> None:
    definition = OpenMetadataServicePlugin().service_definition

    assert definition["image"] == "phlo/openmetadata:1.13.1-java-patches"
    assert definition["build"] == {
        "context": ".",
        "dockerfile": "openmetadata/Dockerfile",
    }
    assert "OPENMETADATA_VERSION" not in definition["env_vars"]


def test_openmetadata_mysql_builds_the_updated_stable_database_image() -> None:
    raw = resources.files("phlo_openmetadata").joinpath("openmetadata-mysql-setup.yaml").read_text()
    definition = yaml.safe_load(raw)

    assert definition["image"] == "phlo/openmetadata-db:1.13.1-ol8.10"
    assert definition["build"] == {
        "context": ".",
        "dockerfile": "openmetadata-mysql/Dockerfile",
    }
