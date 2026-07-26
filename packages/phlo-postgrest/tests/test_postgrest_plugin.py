"""PostgREST generated service contracts."""

from importlib import resources

from phlo_postgrest.plugin import PostgrestServicePlugin


def test_postgrest_builds_a_minimal_stable_runtime_image() -> None:
    definition = PostgrestServicePlugin().service_definition

    assert definition["image"] == "ghcr.io/phlohouse/phlo-postgrest:14.15-security-patches"
    assert definition["build"] == {
        "context": ".",
        "dockerfile": "postgrest/Dockerfile",
    }
    assert "POSTGREST_VERSION" not in definition["env_vars"]
    assert {"source": "Dockerfile", "dest": "postgrest/Dockerfile"} in definition["files"]

    dockerfile = resources.files("phlo_postgrest").joinpath("Dockerfile").read_text()
    assert "postgrest/postgrest:v14.15@sha256:" in dockerfile
    assert "rm -f /usr/bin/pebble" in dockerfile
    assert dockerfile.rstrip().endswith('CMD ["postgrest"]')
