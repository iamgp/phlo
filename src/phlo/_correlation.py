"""Provider-neutral resolution of single-project runtime identity."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectIdentity:
    """Resolved project identity and an explicit gap reason when unresolved."""

    project_id: str | None
    error: str | None = None


def resolve_project_identity(
    tags: Mapping[str, object] | None = None,
    configured_project: str | None = None,
) -> ProjectIdentity:
    """Resolve tags and configured identity without allowing silent disagreement."""
    tag_values = {
        str(key): str(value).strip()
        for key, value in (tags or {}).items()
        if value is not None and str(value).strip()
    }
    tagged = tag_values.get("phlo/project_id")
    configured = configured_project.strip() if configured_project else None
    if tagged and configured and tagged != configured:
        return ProjectIdentity(None, "project_conflict")
    project_id = tagged or configured
    return ProjectIdentity(project_id, None if project_id else "project_missing")
