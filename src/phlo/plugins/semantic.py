from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Protocol, runtime_checkable


@dataclass(frozen=True)
class SemanticModel:
    name: str
    description: str | None = None
    sql: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class SemanticLayerProvider(Protocol):
    def list_models(self) -> Iterable[SemanticModel]:
        ...

    def get_model(self, name: str) -> SemanticModel | None:
        ...
