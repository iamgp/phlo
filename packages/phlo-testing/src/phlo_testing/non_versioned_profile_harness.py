"""Lightweight non-versioned profile harness built on DuckDB and dbt."""

from __future__ import annotations

import contextlib
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from phlo.logging import get_logger


def _find_dbt_executable() -> str | None:
    candidate = Path(sys.executable).parent / "dbt"
    if candidate.exists():
        return str(candidate)
    return shutil.which("dbt")


def _is_missing_duckdb_adapter(output: str) -> bool:
    normalized = output.lower()
    patterns = (
        "could not find adapter type duckdb",
        "adapter type duckdb is not installed",
        "no module named 'dbt.adapters.duckdb'",
        "module not found: dbt.adapters.duckdb",
        "adapter not found",
    )
    return "duckdb" in normalized and any(pattern in normalized for pattern in patterns)


def _assert_duckdb_adapter_available(dbt_executable: str, project_dir: Path) -> None:
    env = {**os.environ, "DBT_PROFILES_DIR": str(project_dir)}
    result = subprocess.run(
        [dbt_executable, "debug", "--profiles-dir", str(project_dir)],
        cwd=project_dir,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    combined_output = "\n".join((result.stdout, result.stderr))
    if _is_missing_duckdb_adapter(combined_output):
        raise RuntimeError("dbt-duckdb adapter not installed")
    if result.returncode != 0:
        raise RuntimeError(f"dbt debug failed for non-versioned harness:\n{combined_output}")


@dataclass(slots=True)
class NonVersionedProfileHarness:
    """Local DuckDB-backed harness for a non-versioned profile."""

    project_dir: Path
    duckdb_path: Path
    dbt_executable: str

    def ingest_rows(self, table_name: str, rows: list[dict[str, Any]]) -> None:
        """Create or replace a raw DuckDB table from row dictionaries."""
        if "." not in table_name:
            raise ValueError("Expected schema-qualified table name like 'raw.posts'")
        schema_name, table_name_only = table_name.split(".", 1)
        dataframe = pd.DataFrame(rows)
        connection = duckdb.connect(str(self.duckdb_path))
        try:
            connection.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
            connection.register("phlo_ingest_rows", dataframe)
            connection.execute(
                f"CREATE OR REPLACE TABLE {schema_name}.{table_name_only} AS "
                "SELECT * FROM phlo_ingest_rows"
            )
        finally:
            connection.close()

    def query(self, query: str) -> list[tuple[Any, ...]]:
        """Execute a DuckDB SQL query against the local profile database."""
        connection = duckdb.connect(str(self.duckdb_path))
        try:
            return connection.execute(query).fetchall()
        finally:
            connection.close()

    def query_scalar(self, query: str) -> Any:
        """Execute a SQL query and return the first scalar value."""
        rows = self.query(query)
        if not rows:
            return None
        return rows[0][0]

    def run_transform(self) -> Any:
        """Run the dbt transform project against the local DuckDB profile."""
        from phlo_dbt.transformer import DbtTransformer

        transformer = DbtTransformer(
            context=None,
            logger=get_logger("phlo_testing.non_versioned_profile"),
            project_dir=self.project_dir,
            profiles_dir=self.project_dir,
            target="dev",
            dbt_executable=self.dbt_executable,
        )
        return transformer.run_transform(partition_key=None, parameters={"generate_docs": False})

    def cleanup(self) -> None:
        """Remove the temporary harness directory unless kept by the caller."""
        with contextlib.suppress(Exception):
            shutil.rmtree(self.project_dir)


def bootstrap_non_versioned_profile_harness(
    *,
    project_dir: Path | None = None,
) -> NonVersionedProfileHarness:
    """Create a local DuckDB-backed dbt project for non-versioned profile tests."""
    target_project_dir = project_dir or Path(tempfile.mkdtemp(prefix="phlo-non-versioned-"))
    dbt_executable = _find_dbt_executable()
    if dbt_executable is None:
        raise RuntimeError("dbt CLI not available for non-versioned profile tests")

    duckdb_path = target_project_dir / "profile.duckdb"
    target_project_dir.mkdir(parents=True, exist_ok=True)

    (target_project_dir / "dbt_project.yml").write_text(
        """name: phlo_non_versioned\nversion: 1.0.0\nconfig-version: 2\nprofile: phlo_non_versioned\nmodel-paths: [\"models\"]\nmodels:\n  phlo_non_versioned:\n    marts:\n      +materialized: table\n"""
    )
    (target_project_dir / "profiles.yml").write_text(
        f"""phlo_non_versioned:\n  target: dev\n  outputs:\n    dev:\n      type: duckdb\n      path: {duckdb_path}\n      threads: 1\n"""
    )
    (target_project_dir / "models" / "sources").mkdir(parents=True, exist_ok=True)
    (target_project_dir / "models" / "marts").mkdir(parents=True, exist_ok=True)
    (target_project_dir / "models" / "sources" / "raw.yml").write_text(
        """version: 2\n\nsources:\n  - name: raw\n    schema: raw\n    tables:\n      - name: posts\n"""
    )
    (target_project_dir / "models" / "marts" / "posts_mart.sql").write_text(
        """{{ config(materialized='table', schema='marts') }}\nselect id, title, body from {{ source('raw', 'posts') }}\n"""
    )

    _assert_duckdb_adapter_available(dbt_executable, target_project_dir)
    return NonVersionedProfileHarness(
        project_dir=target_project_dir,
        duckdb_path=duckdb_path,
        dbt_executable=dbt_executable,
    )


__all__ = [
    "NonVersionedProfileHarness",
    "bootstrap_non_versioned_profile_harness",
]
