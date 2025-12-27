"""Semantic layer interfaces for downstream model providers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Protocol, runtime_checkable


@dataclass(frozen=True)
class SemanticModel:
    """Semantic model definition for downstream consumers."""

    name: str
    description: str | None = None
    sql: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class SemanticLayerProvider(Protocol):
    """Protocol for providers exposing semantic models."""

    def list_models(self) -> Iterable[SemanticModel]: ...

    def get_model(self, name: str) -> SemanticModel | None: ...
