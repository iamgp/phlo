"""Shared helpers for terse flow authoring decorators."""

from __future__ import annotations

import inspect
import re
from collections.abc import Callable, Iterable
from typing import Any

from phlo.capabilities import AssetSpec, MaterializeResult, RunSpec
from phlo.capabilities.runtime import RuntimeContext
from phlo.contracts import SLA, Consumer, normalize_consumers, serialize_consumers, serialize_sla


def asset_key(prefix: str, name: str) -> str:
    """Build a stable asset key from a dotted table or target name."""
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").lower()
    return f"{prefix}_{normalized}"


def contract_metadata(
    *,
    owner: str | None = None,
    consumers: list[Consumer | str] | None = None,
    sla: SLA | None = None,
) -> dict[str, Any]:
    """Build common owner, consumer, and SLA metadata."""
    return {
        "owner": owner,
        "consumers": serialize_consumers(normalize_consumers(consumers)),
        "sla": serialize_sla(sla),
    }


def build_run(fn: Callable[..., Any]) -> RunSpec:
    """Create a generic run spec around a user-authored function."""

    def _run(context: RuntimeContext) -> Iterable[MaterializeResult]:
        result = _call_with_optional_context(fn, context)
        yield MaterializeResult(metadata={"result": result}, status="success")

    return RunSpec(fn=_run)


def _call_with_optional_context(fn: Callable[..., Any], context: RuntimeContext) -> Any:
    signature = inspect.signature(fn)
    required_parameters = [
        parameter
        for parameter in signature.parameters.values()
        if parameter.default is inspect.Parameter.empty
        and parameter.kind
        in {inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD}
    ]
    if required_parameters:
        return fn(context)
    return fn()


def append_asset(registry: list[AssetSpec], asset: AssetSpec) -> None:
    """Register an asset in a module-local registry."""
    registry.append(asset)
