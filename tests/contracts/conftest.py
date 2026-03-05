"""Fixtures for profile-level contract tests."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from phlo_testing.profile_harness import (
    bootstrap_bundled_stack_harness,
    bundled_stack_contract_enabled,
)


@pytest.fixture(scope="session")
def bundled_stack_harness() -> Iterator:
    """Boot the real bundled stack when contract tests are explicitly enabled."""
    if not bundled_stack_contract_enabled():
        pytest.skip("Set PHLO_RUN_BUNDLED_STACK_CONTRACT=1 to run bundled-stack contract tests")

    harness = bootstrap_bundled_stack_harness(stream_output=True)
    try:
        yield harness
    finally:
        harness.cleanup(stream_output=True)
