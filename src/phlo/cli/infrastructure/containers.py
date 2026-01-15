from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class DagsterContainerCandidates:
    configured: str
    new: str
    legacy: str


def dagster_container_candidates(
    project_name: str, configured_name: str | None
) -> DagsterContainerCandidates:
    configured = configured_name or ""
    new = f"{project_name}-dagster-1"
    legacy = f"{project_name}-dagster-webserver-1"
    return DagsterContainerCandidates(configured=configured, new=new, legacy=legacy)


def select_first_existing(candidates: Iterable[str], existing: Iterable[str]) -> str | None:
    existing_set = set(existing)
    for candidate in candidates:
        if candidate and candidate in existing_set:
            return candidate
    return None
