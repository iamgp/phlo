"""Assistant context bundle models."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_DSN_RE = re.compile(r"\b[a-z][a-z0-9+.-]*://\S+", re.IGNORECASE)
_AUTHORIZATION_BEARER_RE = re.compile(
    r"\b(authorization)(\s*:?\s+bearer)\s+\S+",
    re.IGNORECASE,
)
_BEARER_RE = re.compile(r"\b(bearer)\b\s+\S+", re.IGNORECASE)
_KEY_VALUE_SECRET_RE = re.compile(
    r"""\b([\w-]*(?:password|passwd|token|secret|api[_-]?key|credential)[\w-]*)\b\s*[:=]\s*(?:"[^"]*"|'[^']*'|[^\s,;]+)""",
    re.IGNORECASE,
)


def _redact(value: str) -> str:
    value = _DSN_RE.sub("<redacted-dsn>", value)
    value = _KEY_VALUE_SECRET_RE.sub(lambda match: f"{match.group(1)}=<redacted>", value)
    value = _AUTHORIZATION_BEARER_RE.sub(r"\1\2 <redacted>", value)
    return _BEARER_RE.sub(r"\1 <redacted>", value)


def _redact_facts(facts: dict[str, str]) -> dict[str, str]:
    redacted: dict[str, str] = {}
    collisions: dict[str, int] = {}
    for key, value in facts.items():
        redacted_key = _redact(key)
        if redacted_key in redacted:
            collisions[redacted_key] = collisions.get(redacted_key, 1) + 1
            redacted_key = f"{redacted_key} ({collisions[redacted_key]})"
        redacted[redacted_key] = _redact(value)
    return redacted


@dataclass(frozen=True, slots=True)
class AssistantContextBundle:
    title: str
    facts: dict[str, str] = field(default_factory=dict)
    suggested_actions: tuple[str, ...] = ()

    def to_read_model(self) -> dict[str, Any]:
        return {
            "title": _redact(self.title),
            "facts": _redact_facts(self.facts),
            "suggested_actions": [_redact(action) for action in self.suggested_actions],
        }

    def to_mcp_payload(self) -> dict[str, Any]:
        """Serialize context for MCP tools without granting execution privileges."""
        return {"kind": "phlo.assistant.context.v1", "payload": self.to_read_model()}

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
