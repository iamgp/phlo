"""Non-versioned profile contract checks."""

from __future__ import annotations

import pytest
from phlo_testing.non_versioned_profile_harness import NonVersionedProfileHarness

pytestmark = pytest.mark.integration


def test_non_versioned_profile_ingest_and_transform_without_refs(
    non_versioned_profile_harness: NonVersionedProfileHarness,
) -> None:
    """Core ingest and transform composition should work without branch-aware routing."""
    non_versioned_profile_harness.ingest_rows(
        "raw.posts",
        [
            {"id": 1, "title": "hello", "body": "world"},
            {"id": 2, "title": "goodbye", "body": "moon"},
        ],
    )

    raw_count = non_versioned_profile_harness.query_scalar("SELECT count(*) FROM raw.posts")
    assert raw_count == 2

    result = non_versioned_profile_harness.run_transform()
    assert result.status == "success", result.error

    mart_count = non_versioned_profile_harness.query_scalar("SELECT count(*) FROM marts.posts_mart")
    assert mart_count == raw_count
