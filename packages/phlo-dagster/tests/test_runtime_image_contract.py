from __future__ import annotations

from importlib import resources


def test_dagster_runtime_image_installs_prerelease_phlo_with_postgres_driver() -> None:
    dockerfile = resources.files("phlo_dagster").joinpath("Dockerfile").read_text()

    assert dockerfile.startswith("FROM python:3.12-slim")
    assert (
        'uv pip install --system --no-deps --prerelease explicit "phlo==$PHLO_VERSION"'
        in dockerfile
    )
    assert "PHLO_PRERELEASE_REQUIREMENTS" in dockerfile
    assert (
        'uv pip install --system --prerelease explicit "phlo[defaults]==$PHLO_VERSION"'
        in dockerfile
    )
    assert 'dagster-postgres "psycopg[binary]"' in dockerfile


def test_dagster_runtime_entrypoint_installs_mounted_project() -> None:
    entrypoint = resources.files("phlo_dagster").joinpath("entrypoint.sh").read_text()

    assert "if [ -f /app/pyproject.toml ]; then" in entrypoint
    assert "uv pip install --system -e /app" in entrypoint
