"""Semantic layer interfaces for downstream model providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Iterable


@dataclass(frozen=True)
class SemanticModel:
    """Semantic model definition for downstream consumers."""

    name: str
    description: str | None = None
    sql: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class SemanticLayerProvider(ABC):
    """Base class for providers exposing semantic models."""

    @abstractmethod
    def list_models(self) -> Iterable[SemanticModel]:
        """Return all semantic models exposed by this provider."""
        raise NotImplementedError

    @abstractmethod
    def get_model(self, name: str) -> SemanticModel | None:
        """Return a semantic model by name when present."""
        raise NotImplementedError
