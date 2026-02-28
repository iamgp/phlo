"""Default schema change classification helper.

Provides conservative (lowest-common-denominator) classification rules that
storage providers can override via ``SchemaMigrator.classify_change``.
"""

from __future__ import annotations

from typing import Any

_DEFAULT_CLASSIFICATIONS: dict[str, str] = {
    "add": "safe",
    "drop": "breaking",
    "rename": "warning",
    "widen_type": "safe",
    "narrow_type": "breaking",
    "reorder": "safe",
    "nullability_relaxed": "safe",
    "nullability_tightened": "breaking",
}

CLASSIFICATION_ORDER = ("safe", "warning", "breaking")


def default_classify_change(change_type: str, **details: Any) -> str:
    """Classify a schema change using conservative defaults.

    Args:
        change_type: One of the recognised change type strings.
        **details: Extra context (e.g. ``nullable``, ``has_default``).

    Returns:
        Classification string: ``"safe"``, ``"warning"``, or ``"breaking"``.
    """
    if change_type == "add":
        nullable = details.get("nullable", True)
        has_default = details.get("has_default", False)
        if not nullable and not has_default:
            return "breaking"
        if not nullable and has_default:
            return "warning"
        return "safe"

    return _DEFAULT_CLASSIFICATIONS.get(change_type, "breaking")


def worst_classification(classifications: list[str]) -> str:
    """Return the most severe classification from a list.

    Args:
        classifications: List of classification strings.

    Returns:
        The worst (most severe) classification present.
    """
    if not classifications:
        return "safe"
    worst_idx = max(CLASSIFICATION_ORDER.index(c) for c in classifications)
    return CLASSIFICATION_ORDER[worst_idx]
