"""Tests for backend compiler coverage of canonical actions."""

from __future__ import annotations

from phlo.rbac.compiler import COMPILER_REGISTRY
from phlo.rbac.models import CANONICAL_ACTIONS


def test_every_canonical_action_has_at_least_one_compiler():
    """Every canonical action must be supported by at least one backend compiler."""
    unsupported = set()
    for action in CANONICAL_ACTIONS:
        supported_by_any = any(
            cls(backend=None).supports_action(action) for cls in COMPILER_REGISTRY.values()
        )
        if not supported_by_any:
            unsupported.add(action)

    assert not unsupported, f"Actions without any compiler support: {unsupported}"


def test_compiler_registry_not_empty():
    """At least one backend compiler must be registered."""
    assert len(COMPILER_REGISTRY) > 0


def test_compiler_coverage_report():
    """Generate a coverage report for documentation purposes."""
    report: dict[str, dict[str, bool]] = {}

    for action in CANONICAL_ACTIONS:
        report[action] = {}
        for name, cls in sorted(COMPILER_REGISTRY.items()):
            compiler = cls(backend=None)
            report[action][name] = compiler.supports_action(action)

    for name, cls in sorted(COMPILER_REGISTRY.items()):
        compiler = cls(backend=None)
        supported = [a for a in CANONICAL_ACTIONS if compiler.supports_action(a)]
        print(f"{name}: {len(supported)}/{len(CANONICAL_ACTIONS)}")

    print("\nCoverage matrix:")
    for action in sorted(CANONICAL_ACTIONS):
        row = [f"{action:20}"]
        for name in sorted(COMPILER_REGISTRY.keys()):
            row.append("✓" if report[action][name] else "—")
        print("  ".join(row))
