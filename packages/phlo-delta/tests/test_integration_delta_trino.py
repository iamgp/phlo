"""Integration test: phlo-delta + Trino + dbt-style transform.

Spins up MinIO + Hive Metastore + Trino via docker compose, uses
``phlo_delta.resource.DeltaResource`` to write a Delta table, then
queries it through ``phlo_trino.resource.TrinoResource`` and runs a
CTAS transform (the exact SQL that dbt generates).

Requires Docker.  Run with:

    pytest -m integration packages/phlo-delta/tests/test_integration_delta_trino.py -v
"""

from __future__ import annotations

# ruff: noqa: E402

import os
from contextlib import suppress
from subprocess import CalledProcessError, TimeoutExpired, run
import time
from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
import pyarrow as pa
import pytest

pytestmark = pytest.mark.integration

from phlo_delta.resource import DeltaResource

if TYPE_CHECKING:
    from phlo_trino.resource import TrinoResource

COMPOSE_DIR = Path(__file__).parent / "compose"
COMPOSE_TIMEOUT_SECONDS = 300

# Test data -------------------------------------------------------------------

SCHEMA = pa.schema(
    [
        pa.field("id", pa.int64(), nullable=False),
        pa.field("user_id", pa.int64()),
        pa.field("title", pa.string()),
        pa.field("body", pa.string()),
    ]
)

TEST_DF = pd.DataFrame(
    {
        "id": [1, 2, 3, 4, 5],
        "user_id": [10, 20, 10, 30, 20],
        "title": ["First", "Second", "Third", "Fourth", "Fifth"],
        "body": ["body-1", "body-2", "body-3", "body-4", "body-5"],
    }
)


# Helpers ---------------------------------------------------------------------


def _wait_for_url(url: str, *, timeout: int = 120) -> None:
    """Poll a URL until it returns a successful response."""
    from urllib.error import URLError
    from urllib.request import Request, urlopen

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            req = Request(url, method="GET")
            with urlopen(req, timeout=3) as resp:
                if 200 <= resp.status < 400:
                    return
        except (URLError, OSError):
            pass
        time.sleep(2)
    raise TimeoutError(f"{url} not ready after {timeout}s")


def _client_host(host: str) -> str:
    """Return a host address usable by clients running on the test host."""
    return "localhost" if host in {"0.0.0.0", "::"} else host


class ComposeStack:
    """Small docker compose wrapper for this integration fixture."""

    def __init__(self) -> None:
        self.project_name = f"phlo_delta_test_{os.getpid()}"

    def _compose(self, *args: str) -> str:
        result = run(
            [
                "docker",
                "compose",
                "-p",
                self.project_name,
                "-f",
                str(COMPOSE_DIR / "docker-compose.yml"),
                *args,
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=COMPOSE_TIMEOUT_SECONDS,
        )
        return result.stdout.strip()

    def start(self) -> None:
        self._compose("up", "-d")

    def stop(self) -> None:
        self._compose("down", "-v", "--remove-orphans")

    def get_service_host(self, service: str, port: int) -> str:
        _ = service, port
        return "localhost"

    def get_service_port(self, service: str, port: int) -> int:
        output = self._compose("port", service, str(port))
        return int(output.rsplit(":", 1)[1])


# Fixtures --------------------------------------------------------------------


@pytest.fixture(scope="module")
def stack() -> Generator[ComposeStack]:
    """Boot the MinIO + Trino compose stack (file-based metastore)."""
    compose = ComposeStack()
    try:
        compose.start()
    except (CalledProcessError, FileNotFoundError, TimeoutExpired) as exc:
        with suppress(CalledProcessError, FileNotFoundError, TimeoutExpired):
            compose.stop()
        pytest.skip(f"Docker Compose is not available for this integration test: {exc}")
    try:
        trino_host = _client_host(compose.get_service_host("trino", 8080))
        trino_port = compose.get_service_port("trino", 8080)
        _wait_for_url(f"http://{trino_host}:{trino_port}/v1/info", timeout=180)
        yield compose
    finally:
        compose.stop()


@pytest.fixture(scope="module")
def delta_resource(stack: ComposeStack, monkeypatch_module) -> Generator[DeltaResource]:
    """Return a DeltaResource configured to talk to the compose MinIO."""
    from phlo_delta.resource import DeltaResource
    from phlo_delta.settings import get_settings

    minio_host = _client_host(stack.get_service_host("minio", 9000))
    minio_port = stack.get_service_port("minio", 9000)
    endpoint = f"http://{minio_host}:{minio_port}"

    monkeypatch_module.setenv("DELTA_S3_ENDPOINT", endpoint)
    monkeypatch_module.setenv("DELTA_S3_ACCESS_KEY", "minio")
    monkeypatch_module.setenv("DELTA_S3_SECRET_KEY", "minio123")
    monkeypatch_module.setenv("DELTA_WAREHOUSE_PATH", "s3://lake/warehouse/delta")
    monkeypatch_module.setenv("DELTA_S3_ALLOW_UNSAFE_RENAME", "true")

    get_settings.cache_clear()
    try:
        yield DeltaResource()
    finally:
        get_settings.cache_clear()


@pytest.fixture(scope="module")
def trino(stack: ComposeStack) -> TrinoResource:
    """Return a TrinoResource pointed at the compose Trino."""
    from phlo_trino.resource import TrinoResource

    trino_host = _client_host(stack.get_service_host("trino", 8080))
    trino_port = stack.get_service_port("trino", 8080)
    return TrinoResource(host=trino_host, port=trino_port, user="test", catalog="delta")


@pytest.fixture(scope="module")
def monkeypatch_module():
    """Module-scoped monkeypatch (pytest's builtin is function-scoped)."""
    saved: dict[str, str | None] = {}

    class _MP:
        def setenv(self, key: str, value: str) -> None:
            if key not in saved:
                saved[key] = os.environ.get(key)
            os.environ[key] = value

    mp = _MP()
    yield mp

    for key, original in saved.items():
        if original is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original


@pytest.fixture(scope="module")
def staged_parquet(tmp_path_factory) -> Path:
    """Write test data to a parquet file for ingestion."""
    path = tmp_path_factory.mktemp("delta_test") / "posts.parquet"
    TEST_DF.to_parquet(path, index=False)
    return path


# Tests -----------------------------------------------------------------------


def test_delta_resource_write_and_trino_query(
    delta_resource: DeltaResource,
    trino: TrinoResource,
    staged_parquet: Path,
) -> None:
    """End-to-end: DeltaResource writes → TrinoResource queries → CTAS transform."""

    # 1. Use DeltaResource to create a Delta table and append data
    dt = delta_resource.ensure_table(
        table_name="raw.posts",
        schema=SCHEMA,
    )
    assert dt is not None

    result = delta_resource.append_parquet(
        table_name="raw.posts",
        data_path=str(staged_parquet),
    )
    assert result["rows_inserted"] == 5

    # 2. Wait for Trino delta catalog to be available
    trino.wait_ready(timeout=60)

    # 3. Create schema and register the Delta table in Trino
    trino.execute("CREATE SCHEMA IF NOT EXISTS delta.raw")
    table_uri = delta_resource.table_uri("raw.posts")
    trino.execute(
        f"""
        CALL delta.system.register_table(
            schema_name => 'raw',
            table_name  => 'posts',
            table_location => '{table_uri}'
        )
        """
    )

    # 4. Query the raw Delta table via TrinoResource
    rows = trino.execute("SELECT count(*) FROM raw.posts", schema="raw")
    row_count = rows[0][0]
    assert row_count == 5, f"Expected 5 rows, got {row_count}"

    # 5. Verify column data round-trips correctly
    rows = trino.execute(
        "SELECT id, title FROM raw.posts ORDER BY id",
        schema="raw",
    )
    assert list(rows[0]) == [1, "First"]
    assert list(rows[4]) == [5, "Fifth"]

    # 6. dbt-style CTAS transform: aggregate posts per user
    trino.execute("CREATE SCHEMA IF NOT EXISTS delta.marts")
    trino.execute(
        f"""
        CREATE TABLE delta.marts.user_post_summary
        WITH (location = '{delta_resource.table_uri("marts.user_post_summary")}')
        AS
        SELECT
            user_id,
            count(*) AS post_count,
            array_join(array_agg(title ORDER BY id), ', ') AS titles
        FROM delta.raw.posts
        GROUP BY user_id
        """
    )

    # 7. Query the transformed mart table
    mart_rows = trino.execute(
        "SELECT user_id, post_count FROM delta.marts.user_post_summary ORDER BY user_id",
    )
    assert len(mart_rows) == 3, f"Expected 3 user groups, got {len(mart_rows)}"

    result_map = {row[0]: row[1] for row in mart_rows}
    assert result_map[10] == 2
    assert result_map[20] == 2
    assert result_map[30] == 1

    # 8. Verify DeltaResource can read the table stats back
    from deltalake import DeltaTable

    dt = delta_resource.get_table("raw.posts")
    assert isinstance(dt, DeltaTable)

    # 9. Verify DeltaResource list_snapshots (Delta versions)
    versions = delta_resource.list_snapshots(table_name="raw.posts")
    assert len(versions) >= 1
