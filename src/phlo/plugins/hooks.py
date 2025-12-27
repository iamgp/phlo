"""Hook plugin interfaces and registration types."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Iterable, Protocol, runtime_checkable

from phlo.hooks.events import HookEvent
from phlo.plugins.base import Plugin


class FailurePolicy(str, Enum):
    """Failure handling policy for hook handlers."""

    IGNORE = "ignore"
    LOG = "log"
    RAISE = "raise"


@dataclass(frozen=True)
class HookFilter:
    """Filter criteria for deciding whether a hook should run."""

    event_types: set[str] | None = None
    asset_keys: set[str] | None = None
    tags: dict[str, str] | None = None

    def __post_init__(self) -> None:
        """Normalize iterable fields to sets for efficient matching."""

        if self.event_types is not None:
            object.__setattr__(self, "event_types", set(self.event_types))
        if self.asset_keys is not None:
            object.__setattr__(self, "asset_keys", set(self.asset_keys))


@dataclass(frozen=True)
class HookRegistration:
    """Registration details for a hook handler."""

    hook_name: str
    handler: Callable[[HookEvent], None] | "HookHandler"
    priority: int = 100
    filters: HookFilter | None = None
    failure_policy: FailurePolicy = FailurePolicy.LOG


@runtime_checkable
class HookProvider(Protocol):
    """Protocol for plugins that expose hook registrations."""

    def get_hooks(self) -> Iterable[HookRegistration]: ...


@runtime_checkable
class HookHandler(Protocol):
    """Protocol for handler objects implementing hook dispatch."""

    def handle_event(self, event: HookEvent) -> None: ...


class HookPlugin(Plugin, HookProvider):
    """Base class for hook-only plugins."""

    def get_hooks(self) -> Iterable[HookRegistration]:
        """Return hook registrations for this plugin."""

        return []
