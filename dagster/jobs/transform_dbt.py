import os
import sys
from contextlib import contextmanager

from dagster import job, op

import openlineage.dbt


@contextmanager
def _temporary_environ(overrides: dict[str, str]):
    """Temporarily update os.environ with overrides."""
    original = {}
    try:
        for key, value in overrides.items():
            original[key] = os.environ.get(key)
            os.environ[key] = value
        yield
    finally:
        for key in overrides:
            if original[key] is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original[key]


def _run_openlineage_dbt_command(args: list[str]) -> None:
    """Invoke openlineage-dbt wrapper with the provided CLI args."""
    namespace = os.getenv("OPENLINEAGE_NAMESPACE", "lakehouse")
    url = os.getenv("OPENLINEAGE_URL", "http://marquez:5000")

    env_overrides = {
        "OPENLINEAGE_URL": url,
        "OPENLINEAGE_NAMESPACE": namespace,
        "DBT_OPENLINEAGE_URL": url,
        "DBT_OPENLINEAGE_NAMESPACE": namespace,
        "DBT_PROFILES_DIR": "/dbt/profiles",
        "DBT_PROJECT_DIR": "/dbt",
    }

    argv_backup = sys.argv[:]
    sys.argv = ["openlineage-dbt", *args]
    try:
        with _temporary_environ(env_overrides):
            return_code = openlineage.dbt.main()
    finally:
        sys.argv = argv_backup

    if return_code != 0:
        raise RuntimeError(
            f"openlineage-dbt exited with status {return_code} for args: {args}"
        )

@op
def dbt_run_all(_context):
    args = [
        "build",
        "--project-dir",
        "/dbt",
        "--profiles-dir",
        "/dbt/profiles",
        "--target",
        os.getenv("DBT_TARGET", "duckdb"),
    ]
    _run_openlineage_dbt_command(args)

@op
def dbt_test_all(_context):
    args = [
        "test",
        "--project-dir",
        "/dbt",
        "--profiles-dir",
        "/dbt/profiles",
        "--target",
        os.getenv("DBT_TARGET", "duckdb"),
    ]
    _run_openlineage_dbt_command(args)

@job(
    resource_defs={}
)
def dbt_build_duckdb_then_marts():
    # In dbt, use selectors to: 1) build duckdb targets, 2) build postgres marts
    dbt_run_all()
    dbt_test_all()
