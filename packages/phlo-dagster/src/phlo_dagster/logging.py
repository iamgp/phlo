"""Dagster-aware logging helpers for Phlo assets.

This module provides structured logging utilities that integrate with
Dagster's execution context. It extracts correlation fields from Dagster
contexts and provides decorators for automatic execution lifecycle logging.

Features:
    - Correlation field extraction: run_id, asset_key, job_name, partition_key
    - Context-aware logger binding
    - Automatic start/end logging decorator
    - Integration with Phlo's structured logging system
    - Context binding and cleanup for log correlation

Dagster Context Support:
    - AssetExecutionContext: Asset materialization runs
    - OpExecutionContext: Generic operation execution
    - OpExecutionContext: Generic operation execution

Correlation Fields:
    - run_id: Dagster run identifier
    - asset_key: Fully qualified asset key path
    - job_name: Job/pipeline name
    - partition_key: Partition identifier (for partitioned assets)

Example:
    Using dagster_logger::

        from phlo_dagster.logging import dagster_logger

        @dg.asset
        def my_asset(context):
            logger = dagster_logger(context)
            logger.info("Processing started", extra={"records": 1000})

    Using with_asset_logging decorator::

        from phlo_dagster.logging import with_asset_logging

        @dg.asset
        @with_asset_logging
        def my_asset(context):
            # Automatic "Asset execution started/completed" logs
            return compute_data()

"""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar

import structlog

from phlo.logging import bind_context, clear_context, get_logger

try:
    from dagster import AssetExecutionContext, OpExecutionContext
except Exception as exc:  # noqa: BLE001 - optional dependency
    raise ImportError("Dagster is required for phlo_dagster.logging") from exc

T = TypeVar("T")


def dagster_logger(
    context: AssetExecutionContext | OpExecutionContext,
) -> structlog.stdlib.BoundLogger:
    """Return a logger with Dagster correlation fields bound.

    Args:
        context: Dagster execution context.

    Returns:
        Bound logger with correlation fields.

    """

    return get_logger(context.__class__.__module__).bind(**get_correlation_fields(context))


def get_correlation_fields(context: AssetExecutionContext | OpExecutionContext) -> dict[str, Any]:
    """Extract correlation fields from Dagster context.

    Returns fields for log correlation:
    - run_id: Dagster run ID
    - asset_key: Asset key path (if available)
    - job_name: Job name
    - partition_key: Partition key (if partitioned)

    Args:
        context: Dagster execution context.

    Returns:
        Dictionary of correlation fields.

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
    """Log a message with Dagster correlation fields via context.log.

    Args:
        context: Dagster execution context.
        message: Log message.
        level: Log level (default: info).
        **extra: Additional log fields.

    Returns:
        None

    """

    correlation = get_correlation_fields(context)
    all_extra = {**correlation, **extra}

    logger = getattr(context.log, level)
    logger(message, extra=all_extra)


def with_asset_logging(
    func: Callable[..., T],
) -> Callable[..., T]:
    """Decorator to add automatic start/end logging with correlation fields.

    Args:
        func: Function to wrap.

    Returns:
        Wrapped function with lifecycle logging.

    """

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

        Raises:
            Exception: Re-raises any exception from the wrapped function.

        """
        correlation = get_correlation_fields(context)
        bind_context(**correlation)

        try:
            context.log.info(
                "Asset execution started",
                extra=correlation,
            )
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
        finally:
            clear_context()

    return wrapper
