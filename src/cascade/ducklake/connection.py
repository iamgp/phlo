from __future__ import annotations

from collections.abc import Iterable, Sequence

from duckdb import DuckDBPyConnection

from .configuration import DuckLakeRuntimeConfig


def _install_extension(conn: DuckDBPyConnection, extension: str) -> None:
    conn.execute(f"INSTALL {extension}")
    conn.execute(f"LOAD {extension}")


def _database_list(conn: DuckDBPyConnection) -> Sequence[tuple]:
    return conn.execute("PRAGMA database_list").fetchall()


def _schema_exists(conn: DuckDBPyConnection, schema: str) -> bool:
    try:
        conn.execute(
            "SELECT 1 FROM information_schema.schemata WHERE schema_name = ? LIMIT 1",
            [schema],
        )
        return conn.fetchone() is not None
    except Exception:
        return False


def configure_ducklake_connection(
    conn: DuckDBPyConnection,
    runtime: DuckLakeRuntimeConfig,
    *,
    ensure_schemas: Iterable[str] | None = None,
    read_only: bool = False,
) -> DuckDBPyConnection:
    """
    Configure a DuckDB connection to use DuckLake with PostgreSQL catalog and object storage.

    This installs required extensions, defines secrets, attaches the catalog, and ensures
    required schemas exist.

    Args:
        conn: Existing DuckDB connection to configure.
        runtime: Pre-computed runtime configuration.
        ensure_schemas: Optional iterable of schemas to create if missing.
        read_only: Attach the DuckLake catalog in read-only mode.

    Returns:
        The configured connection for convenience.
    """

    # Extensions required for DuckLake + PostgreSQL + S3
    for extension in ("ducklake", "httpfs", "postgres"):
        _install_extension(conn, extension)

    # Configure S3/MinIO access for DuckLake data files
    # Note: DuckDB reads AWS_S3_ENDPOINT from environment, so we don't set it here to avoid double http://
    # conn.execute("SET s3_endpoint=?", [endpoint])
    conn.execute("SET s3_url_style=?", [runtime.s3_url_style])
    conn.execute("SET s3_use_ssl=?", ["true" if runtime.minio_use_ssl else "false"])
    conn.execute("SET s3_access_key_id=?", [runtime.minio_access_key])
    conn.execute("SET s3_secret_access_key=?", [runtime.minio_secret_key])
    conn.execute("SET s3_region=?", [runtime.minio_region])

    # Tune DuckLake retry behaviour for concurrent loads
    conn.execute("SET ducklake_max_retry_count=?", [runtime.ducklake_retry_count])
    conn.execute("SET ducklake_retry_wait_ms=?", [runtime.ducklake_retry_wait_ms])
    conn.execute("SET ducklake_retry_backoff=?", [runtime.ducklake_retry_backoff])

    # Secrets for PostgreSQL catalog and MinIO-backed storage
    conn.execute(
        f"""
        CREATE OR REPLACE SECRET {runtime.postgres_secret_name} (
            TYPE postgres,
            HOST '{runtime.postgres_host}',
            PORT '{runtime.postgres_port}',
            DATABASE '{runtime.catalog_database}',
            USER '{runtime.postgres_user}',
            PASSWORD '{runtime.postgres_password}'
        )
        """
    )

    # S3 secret for DuckLake - use endpoint from environment
    conn.execute(
    f"""
    CREATE OR REPLACE SECRET {runtime.s3_secret_name} (
    TYPE s3,
    PROVIDER config,
    KEY_ID '{runtime.minio_access_key}',
    SECRET '{runtime.minio_secret_key}',
    REGION '{runtime.minio_region}',
    ENDPOINT 'minio:9000',
    URL_STYLE '{runtime.s3_url_style}',
    USE_SSL {"TRUE" if runtime.minio_use_ssl else "FALSE"}
    )
    """
    )

    conn.execute(
        f"""
        CREATE OR REPLACE SECRET {runtime.ducklake_secret_name} (
            TYPE ducklake,
            METADATA_PATH '',
            DATA_PATH '{runtime.data_path}',
            METADATA_PARAMETERS MAP {{
                'TYPE': 'postgres',
                'SECRET': '{runtime.postgres_secret_name}'
            }}
        )
        """
    )

    # Attach (or reuse) the DuckLake catalog
    databases = _database_list(conn)
    attached_aliases = {row[1] for row in databases} if databases else set()
    attach_options: list[str] = []
    if read_only:
        attach_options.append("READ_ONLY TRUE")
    else:
        attach_options.append(f"DATA_PATH '{runtime.data_path}'")
        attach_options.append("OVERRIDE_DATA_PATH TRUE")

    options_clause = f" ({', '.join(attach_options)})" if attach_options else ""

    if runtime.catalog_alias not in attached_aliases:
        conn.execute(
            f"ATTACH 'ducklake:{runtime.ducklake_secret_name}' AS {runtime.catalog_alias}"
            f"{options_clause}"
        )

    conn.execute(f"USE {runtime.catalog_alias}")

    main_dataset_schema = runtime.default_dataset

    # Ensure bronze/silver/gold schemas exist
    bootstrap_schemas = {
        runtime.default_dataset,
        runtime.staging_dataset,
        main_dataset_schema,
        "bronze",
        "silver",
        "gold",
        "main_marts",
    }

    if ensure_schemas:
        bootstrap_schemas.update(ensure_schemas)

    for schema in bootstrap_schemas:
        if not schema:
            continue
        try:
            if not _schema_exists(conn, schema):
                conn.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
        except Exception:
            conn.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')

    conn.execute("SET search_path=?", [runtime.default_dataset])

    return conn
