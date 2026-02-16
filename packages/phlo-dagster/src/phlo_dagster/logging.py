"""Dagster-aware logging helpers."""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

import structlog

from phlo.logging import get_logger

try:
    from dagster import AssetExecutionContext, OpExecutionContext
except Exception as exc:  # noqa: BLE001 - optional dependency
    raise ImportError("Dagster is required for phlo_dagster.logging") from exc

T = TypeVar("T")


def dagster_logger(
    context: AssetExecutionContext | OpExecutionContext,
) -> structlog.stdlib.BoundLogger:
    """Return a logger with Dagster correlation fields bound."""

    return get_logger(context.__class__.__module__).bind(**get_correlation_fields(context))


def get_correlation_fields(context: AssetExecutionContext | OpExecutionContext) -> dict[str, Any]:
    """
    Extract correlation fields from Dagster context.

    Returns fields for log correlation:
    - run_id: Dagster run ID
    - asset_key: Asset key path (if available)
    - job_name: Job name
    - partition_key: Partition key (if partitioned)
    """

    fields: dict[str, Any] = {
        "run_id": context.run_id,
    }

    if hasattr(context, "asset_key"):
        fields["asset_key"] = context.asset_key.to_user_string()
    if hasattr(context, "job_name"):
        fields["job_name"] = context.job_name
    if hasattr(context, "partition_key") and context.has_partition_key:
        fields["partition_key"] = context.partition_key

    return fields


def log_with_context(
    context: AssetExecutionContext | OpExecutionContext,
    message: str,
    level: str = "info",
    **extra: Any,
) -> None:
    """Log a message with Dagster correlation fields via context.log."""

    correlation = get_correlation_fields(context)
    all_extra = {**correlation, **extra}

    logger = getattr(context.log, level)
    logger(message, extra=all_extra)


def with_asset_logging(
    func: Callable[..., T],
) -> Callable[..., T]:
    """Decorator to add automatic start/end logging with correlation fields."""

    @wraps(func)
    def wrapper(
        context: AssetExecutionContext | OpExecutionContext, *args: Any, **kwargs: Any
    ) -> T:
        """Execute wrapped asset function with lifecycle logging.

        Args:
            context: Dagster execution context.
            *args: Positional arguments for the wrapped function.
            **kwargs: Keyword arguments for the wrapped function.

        Returns:
            Wrapped function result.
        """
        correlation = get_correlation_fields(context)

        context.log.info(
            "Asset execution started",
            extra=correlation,
        )

        try:
            result = func(context, *args, **kwargs)
            context.log.info(
                "Asset execution completed",
                extra=correlation,
            )
            return result
        except Exception as exc:
            context.log.error(
                f"Asset execution failed: {exc}",
                extra={**correlation, "error": str(exc)},
            )
            raise

    return wrapper
