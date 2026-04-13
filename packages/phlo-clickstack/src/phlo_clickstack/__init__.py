"""Phlo ClickStack package for observability backend.

This package provides a ClickStack service plugin for Phlo, bundling
ClickHouse for observability data storage and querying.

Exports:
    ClickStackServicePlugin: Service plugin for ClickStack.
    ClickStackCliPlugin: CLI plugin for ClickStack commands.
    ClickStackSurfaceAdapter: Regulated surface adapter for ClickStack CLI.
    get_clickstack_adapter: Get the ClickStack surface adapter singleton.
"""

from phlo_clickstack.authorization import (
    ClickStackSurfaceAdapter,
    get_adapter as get_clickstack_adapter,
)

__all__ = [
    "ClickStackSurfaceAdapter",
    "get_clickstack_adapter",
]
