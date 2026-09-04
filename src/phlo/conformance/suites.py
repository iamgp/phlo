"""Closed conformance suite registry and run configuration.

The registry is frozen by ADR 0053 concern 7: ``query_engine.v1`` is the
only approved suite. Cases are Phlo-owned; providers never supply test
logic. Adding a suite or a case is a decision recorded in an ADR, not a
code change — ``register_suite`` exists only for that future decision
path and is not called anywhere in this repository.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType


class UnknownSuiteError(KeyError):
    """Raised when a suite id is not in the closed registry."""


class SuiteDefinition:
    """One frozen conformance suite."""

    __slots__ = (
        "suite_id",
        "capability_type",
        "entry_point_group",
        "cases",
        "evidence_validity_days",
    )

    def __init__(
        self,
        *,
        suite_id: str,
        capability_type: str,
        entry_point_group: str,
        cases: tuple[str, ...],
        evidence_validity_days: int,
    ) -> None:
        self.suite_id = suite_id
        self.capability_type = capability_type
        self.entry_point_group = entry_point_group
        self.cases = tuple(cases)
        self.evidence_validity_days = evidence_validity_days

    def __repr__(self) -> str:  # pragma: no cover - debug convenience
        return f"SuiteDefinition(suite_id={self.suite_id!r}, cases={self.cases!r})"


#: ``query_engine.v1`` — the sole approved suite (ADR 0053 concern 7).
#: Cases exercise the Phlo-owned ``QueryEngine`` protocol contract:
#: structural identity, literal execution, error surfacing, and bounded
#: offset paging. The names are frozen; worker case logic lives in
#: ``worker.py`` and must stay in lockstep with this tuple.
QUERY_ENGINE_V1 = SuiteDefinition(
    suite_id="query_engine.v1",
    capability_type="query_engine",
    entry_point_group="phlo.plugins.resources",
    cases=(
        "spec_identity",
        "execute_literal_select",
        "execute_error_surfaces",
        "preview_bounded_page",
        "preview_offset_pages",
    ),
    evidence_validity_days=90,
)

_SUITES: Mapping[str, SuiteDefinition] = MappingProxyType(
    {QUERY_ENGINE_V1.suite_id: QUERY_ENGINE_V1}
)


def get_suite(suite_id: str) -> SuiteDefinition:
    """Return the suite definition, refusing anything outside the registry."""
    suite = _SUITES.get(suite_id)
    if suite is None:
        raise UnknownSuiteError(
            f"conformance suite {suite_id!r} is not in the closed registry; "
            f"approved suites: {sorted(_SUITES)!r}"
        )
    return suite


def suite_ids() -> tuple[str, ...]:
    """Return every approved suite id."""
    return tuple(sorted(_SUITES))


class RunConfig:
    """Controller-side run configuration for one conformance run."""

    __slots__ = ("worker_timeout_seconds", "pip_timeout_seconds")

    def __init__(
        self,
        *,
        worker_timeout_seconds: int = 300,
        pip_timeout_seconds: int = 300,
    ) -> None:
        self.worker_timeout_seconds = worker_timeout_seconds
        self.pip_timeout_seconds = pip_timeout_seconds


__all__ = ["RunConfig", "SuiteDefinition", "UnknownSuiteError", "get_suite", "suite_ids"]
