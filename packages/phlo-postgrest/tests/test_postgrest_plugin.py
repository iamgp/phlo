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


def test_postgrest_uses_the_project_postgres_credentials() -> None:
    """Generated projects use a random database password, not the template fallback."""
    definition = PostgrestServicePlugin().service_definition

    assert definition["compose"]["environment"]["PGRST_DB_URI"] == (
        "postgresql://${POSTGRES_USER:-phlo}:${POSTGRES_PASSWORD:-phlo}@postgres:5432/"
        "${POSTGRES_DB:-phlo}"
    )
    assert "POSTGREST_VERSION" not in definition["env_vars"]
    assert {"source": "Dockerfile", "dest": "postgrest/Dockerfile"} in definition["files"]

    dockerfile = resources.files("phlo_postgrest").joinpath("Dockerfile").read_text()
    assert "postgrest/postgrest:v14.15@sha256:" in dockerfile
    assert "COPY --from=upstream /bin/postgrest /usr/bin/postgrest" in dockerfile
    assert "rm -f /usr/bin/pebble" in dockerfile
    assert dockerfile.rstrip().endswith('CMD ["postgrest"]')
