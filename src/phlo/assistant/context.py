"""Assistant context bundle models."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_DSN_RE = re.compile(r"^[a-z][a-z0-9+.-]*://\S+$", re.IGNORECASE)
_TOKEN_RE = re.compile(r"(token)=\S+", re.IGNORECASE)


def _redact(value: str) -> str:
    if _DSN_RE.fullmatch(value):
        return "<redacted-dsn>"
    return _TOKEN_RE.sub(r"\1=<redacted>", value)


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
        payload = self.to_read_model()
        facts = payload["facts"]
        lines = [
            f"Incident: {payload['title']}",
            "Facts:",
            *(f"- {key}: {facts[key]}" for key in sorted(facts)),
            "Suggested actions:",
            *(f"- {action}" for action in payload["suggested_actions"]),
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
