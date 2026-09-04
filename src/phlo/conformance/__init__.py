"""Artifact-bound conformance runner (ADR 0053, issue #856).

Phlo-owned conformance tracers execute against an exact candidate
artifact (one wheel + one static descriptor) inside a disposable worker
that loads only candidate-owned entry points, and emit schema-valid
artifact-bound evidence for the ``query_engine.v1`` suite.

The suite registry is closed (ADR 0053 concern 7): ``query_engine.v1``
is the only approved suite, and extending it is a decision, not a code
change. This package makes no support, security, performance, or
production-readiness claims: a passing run can qualify an artifact for
the ``conformance-tested`` tier and nothing above it.
"""

from phlo.conformance.runner import (
    ConformanceBindingError,
    ConformanceRunError,
    run_conformance,
)
from phlo.conformance.suites import (
    RunConfig,
    get_suite,
    suite_ids,
)

__all__ = [
    "ConformanceBindingError",
    "ConformanceRunError",
    "RunConfig",
    "get_suite",
    "run_conformance",
    "suite_ids",
]
