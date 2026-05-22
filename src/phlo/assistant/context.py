"""Assistant context bundle models."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from math import isfinite
from typing import Any

_DSN_RE = re.compile(r"\b[a-z][a-z0-9+.-]*://\S+", re.IGNORECASE)
_AUTHORIZATION_BEARER_RE = re.compile(
    r"\b(authorization)(\s*:?\s+bearer)\s+\S+",
    re.IGNORECASE,
)
_BEARER_RE = re.compile(r"\b(bearer)\b\s+\S+", re.IGNORECASE)
_SECRET_NAME_PATTERN = (
    r"[\w-]*(?:password|passwd|token|secret|api[_-]?key|credential|"
    r"private[_-]?key|signing[_-]?key|encryption[_-]?key)[\w-]*"
)
_KEY_VALUE_SECRET_RE = re.compile(
    rf"""\b({_SECRET_NAME_PATTERN})\b\s*[:=]\s*(?:"[^"]*"|'[^']*'|[^\s,;]+)""",
    re.IGNORECASE,
)
_SECRET_KEY_RE = re.compile(
    r"^(?:password|passwd|token|access[_-]?token|refresh[_-]?token|"
    r"auth[_-]?token|session[_-]?token|client[_-]?secret|secret[_-]?key|"
    r"secret|api[_-]?key|credential|authorization|"
    r"private[_-]?key(?:[_-].*)?|signing[_-]?key(?:[_-].*)?|"
    r"encryption[_-]?key(?:[_-].*)?)$",
    re.IGNORECASE,
)


def _redact(value: str) -> str:
    value = _DSN_RE.sub("<redacted-dsn>", value)
    value = _KEY_VALUE_SECRET_RE.sub(lambda match: f"{match.group(1)}=<redacted>", value)
    value = _AUTHORIZATION_BEARER_RE.sub(r"\1\2 <redacted>", value)
    return _BEARER_RE.sub(r"\1 <redacted>", value)


def _redact_value(value: Any, *, secret_key: bool = False) -> Any:
    if secret_key:
        return "<redacted>"
    if isinstance(value, str):
        return _redact(value)
    if isinstance(value, Mapping):
        return _redact_facts(value)
    if isinstance(value, list):
        return [_redact_value(item) for item in value]
    if isinstance(value, tuple):
        return [_redact_value(item) for item in value]
    if isinstance(value, set):
        return sorted((_redact_value(item) for item in value), key=repr)
    if isinstance(value, float) and not isfinite(value):
        return str(value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return _redact(str(value))


def _redact_facts(facts: Mapping[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    collisions: dict[str, int] = {}
    for key, value in facts.items():
        raw_key = str(key)
        redacted_key = _redact(raw_key)
        if redacted_key in redacted:
            collisions[redacted_key] = collisions.get(redacted_key, 1) + 1
            redacted_key = f"{redacted_key} ({collisions[redacted_key]})"
        redacted[redacted_key] = _redact_value(
            value,
            secret_key=_SECRET_KEY_RE.fullmatch(raw_key) is not None,
        )
    return redacted


@dataclass(frozen=True, slots=True)
class AssistantContextBundle:
    title: str
    facts: dict[str, Any] = field(default_factory=dict)
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
    facts: dict[str, Any],
    suggested_actions: list[str] | tuple[str, ...],
) -> AssistantContextBundle:
    return AssistantContextBundle(
        title=title,
        facts=dict(facts),
        suggested_actions=tuple(suggested_actions),
    )
