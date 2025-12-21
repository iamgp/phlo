"""
Structured Logging for Phlo Assets

Provides context-aware logging with correlation fields for Dagster assets.
Logs are collected by Grafana Alloy and stored in Loki for unified observability.
"""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, TypeVar

if TYPE_CHECKING:
    from dagster import AssetExecutionContext, OpExecutionContext


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

    # Add asset key if available
    if hasattr(context, "asset_key"):
        fields["asset_key"] = context.asset_key.to_user_string()

    # Add job name
    if hasattr(context, "job_name"):
        fields["job_name"] = context.job_name

    # Add partition key if partitioned
    if hasattr(context, "partition_key") and context.has_partition_key:
        fields["partition_key"] = context.partition_key

    return fields


def log_with_context(
    context: AssetExecutionContext | OpExecutionContext,
    message: str,
    level: str = "info",
    **extra: Any,
) -> None:
    """
    Log a message with correlation fields.

    Args:
        context: Dagster execution context
        message: Log message
        level: Log level (debug, info, warning, error)
        **extra: Additional fields to include
    """
    correlation = get_correlation_fields(context)
    all_extra = {**correlation, **extra}

    logger = getattr(context.log, level)
    logger(message, extra=all_extra)


T = TypeVar("T")


def with_asset_logging(
    func: Callable[..., T],
) -> Callable[..., T]:
    """
    Decorator to add automatic start/end logging with correlation fields.

    Example:
        @asset
        @with_asset_logging
        def my_asset(context):
            # Asset logic
            return result
    """

    @wraps(func)
    def wrapper(
        context: AssetExecutionContext | OpExecutionContext, *args: Any, **kwargs: Any
    ) -> T:
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
        except Exception as e:
            context.log.error(
                f"Asset execution failed: {e}",
                extra={**correlation, "error": str(e)},
            )
            raise

    return wrapper
