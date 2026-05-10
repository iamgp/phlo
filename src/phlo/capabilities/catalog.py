"""Shared catalog storage for capability registrations."""

from __future__ import annotations

from collections.abc import Callable, Hashable
from dataclasses import dataclass, field
from typing import Generic, Protocol, TypeVar

SpecT = TypeVar("SpecT")
KeyT = TypeVar("KeyT", bound=Hashable)


class NamedSpec(Protocol):
    name: str


NamedSpecT = TypeVar("NamedSpecT", bound=NamedSpec)


@dataclass(slots=True)
class CapabilityFamily(Generic[SpecT, KeyT]):
    """Registration storage for one capability family."""

    key: Callable[[SpecT], KeyT]
    _items: dict[KeyT, SpecT] = field(default_factory=dict)

    def register(self, spec: SpecT) -> None:
        self._items[self.key(spec)] = spec

    def list(self) -> list[SpecT]:
        return list(self._items.values())

    def clear(self) -> None:
        self._items.clear()


def named_family() -> CapabilityFamily[NamedSpecT, str]:
    return CapabilityFamily(key=lambda spec: spec.name)
