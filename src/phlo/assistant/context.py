"""Assistant context bundle models."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_DSN_RE = re.compile(r"^[a-z][a-z0-9+.-]*://\S+$", re.IGNORECASE)
_TOKEN_RE = re.compile(r"token=\S+")


def _redact(value: str) -> str:
    if _DSN_RE.fullmatch(value):
        return "<redacted-dsn>"
    return _TOKEN_RE.sub("token=<redacted>", value)


@dataclass(frozen=True, slots=True)
class AssistantContextBundle:
    title: str
    facts: dict[str, str] = field(default_factory=dict)
    suggested_actions: tuple[str, ...] = ()

    def to_read_model(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "facts": {key: _redact(value) for key, value in self.facts.items()},
            "suggested_actions": list(self.suggested_actions),
        }

    def to_prompt(self) -> str:
        lines = [
            f"Incident: {self.title}",
            "Facts:",
            *(f"- {key}: {self.facts[key]}" for key in sorted(self.facts)),
            "Suggested actions:",
            *(f"- {action}" for action in self.suggested_actions),
        ]
        return "\n".join(lines)


def build_incident_context(
    *,
    title: str,
    facts: dict[str, str],
    suggested_actions: list[str] | tuple[str, ...],
) -> AssistantContextBundle:
    return AssistantContextBundle(
        title=title,
        facts=dict(facts),
        suggested_actions=tuple(suggested_actions),
    )
