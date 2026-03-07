"""Unit tests for the local non-versioned profile harness."""

from __future__ import annotations

from phlo_testing.non_versioned_profile_harness import NonVersionedProfileHarness


def test_non_versioned_profile_harness_ingests_and_queries(tmp_path) -> None:
    harness = NonVersionedProfileHarness(
        project_dir=tmp_path,
        duckdb_path=tmp_path / "profile.duckdb",
        dbt_executable="dbt",
    )

    harness.ingest_rows(
        "raw.posts",
        [{"id": 1, "title": "hello", "body": "world"}],
    )

    assert harness.query_scalar("SELECT count(*) FROM raw.posts") == 1
    assert harness.query("SELECT title FROM raw.posts") == [("hello",)]
