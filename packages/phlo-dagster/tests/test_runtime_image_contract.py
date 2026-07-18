from __future__ import annotations

from importlib import resources
from pathlib import Path


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


def test_dagster_runtime_image_pins_dbt_when_the_provider_version_is_populated() -> None:
    dockerfile = resources.files("phlo_dagster").joinpath("Dockerfile").read_text()

    assert 'ARG PHLO_DBT_VERSION=""' in dockerfile
    assert (
        'if [ -n "$PHLO_DBT_VERSION" ]; then '
        'PHLO_DBT_REQUIREMENT="phlo-dbt==$PHLO_DBT_VERSION"; fi;'
    ) in dockerfile
    assert (
        'if [ -n "$PHLO_DBT_VERSION" ]; then uv pip install --system --no-index '
        "--no-deps --reinstall --find-links /opt/phlo-wheelhouse "
        '"$PHLO_DBT_REQUIREMENT"; fi;'
    ) in dockerfile
    assert dockerfile.count('"$PHLO_DBT_REQUIREMENT"') == 4
    package_metadata = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text()
    assert '"phlo-dbt' not in package_metadata


def test_dagster_runtime_image_keeps_dbt_unpinned_when_provider_version_is_empty() -> None:
    dockerfile = resources.files("phlo_dagster").joinpath("Dockerfile").read_text()

    assert 'PHLO_DBT_REQUIREMENT="phlo-dbt";' in dockerfile
    assert '"phlo-dbt==$PHLO_DBT_VERSION" dagster-webserver' not in dockerfile
    assert '"phlo[defaults]" "$PHLO_DBT_REQUIREMENT" dagster-webserver' in dockerfile


def test_dagster_runtime_entrypoint_installs_mounted_project() -> None:
    entrypoint = resources.files("phlo_dagster").joinpath("entrypoint.sh").read_text()

    root_guard = 'if [ "$(id -u)" -eq 0 ]; then'
    assert "if [ -f /app/pyproject.toml ]; then" in entrypoint
    assert "uv pip install --system -e /app" in entrypoint
    assert root_guard in entrypoint
    assert entrypoint.index(root_guard) < entrypoint.index("uv pip install --system -e /app")
    non_root_message = 'echo "Non-root mode: using mounted project directly"'
    assert non_root_message in entrypoint
    assert entrypoint.index("uv pip install --system -e /app") < entrypoint.index(non_root_message)
    assert entrypoint.index("fi\n\n# Execute Dagster") > entrypoint.index(non_root_message)
