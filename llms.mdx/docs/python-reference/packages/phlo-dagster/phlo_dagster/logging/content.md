# logging (/docs/python-reference/packages/phlo-dagster/phlo_dagster/logging)



Dagster-aware logging helpers for Phlo assets.

This module provides structured logging utilities that integrate with
Dagster's execution context. It extracts correlation fields from Dagster
contexts and provides decorators for automatic execution lifecycle logging.

Features:

* Correlation field extraction: run\_id, asset\_key, job\_name, partition\_key
* Context-aware logger binding
* Automatic start/end logging decorator
* Integration with Phlo's structured logging system
* Context binding and cleanup for log correlation

Dagster Context Support:

* AssetExecutionContext: Asset materialization runs
* OpExecutionContext: Generic operation execution
* OpExecutionContext: Generic operation execution

Correlation Fields:

* run\_id: Dagster run identifier
* asset\_key: Fully qualified asset key path
* job\_name: Job/pipeline name
* partition\_key: Partition identifier (for partitioned assets)

Example:
Using dagster\_logger::

from phlo\_dagster.logging import dagster\_logger

@dg.asset
def my\_asset(context):
logger = dagster\_logger(context)
logger.info("Processing started", extra=\{"records": 1000})

Using with\_asset\_logging decorator::

from phlo\_dagster.logging import with\_asset\_logging

@dg.asset
@with\_asset\_logging
def my\_asset(context):

Automatic "Asset execution started/completed" logs [#automatic-asset-execution-startedcompleted-logs]

return compute\_data()

<PyAttribute name="&#x22;T&#x22;" type="null" value="&#x22;TypeVar('T')&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;dagster_logger&#x22;" type="&#x22;(context) -> structlog.stdlib.BoundLogger&#x22;">
      Return a logger with Dagster correlation fields bound.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;context&#x22;" type="&#x22;AssetExecutionContext | OpExecutionContext&#x22;" value="undefined">
          Dagster execution context.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;structlog.stdlib.BoundLogger&#x22;">
        Bound logger with correlation fields.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;get_correlation_fields&#x22;" type="&#x22;(context) -> dict[str, Any]&#x22;">
      Extract correlation fields from Dagster context.

      Returns fields for log correlation:

      * run\_id: Dagster run ID
      * asset\_key: Asset key path (if available)
      * job\_name: Job name
      * partition\_key: Partition key (if partitioned)

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;context&#x22;" type="&#x22;AssetExecutionContext | OpExecutionContext&#x22;" value="undefined">
          Dagster execution context.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Dictionary of correlation fields.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;log_with_context&#x22;" type="&#x22;(context, message, level='info', **extra) -> None&#x22;">
      Log a message with Dagster correlation fields via context.log.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;context&#x22;" type="&#x22;AssetExecutionContext | OpExecutionContext&#x22;" value="undefined">
          Dagster execution context.
        </PyParameter>

        <PyParameter name="&#x22;message&#x22;" type="&#x22;str&#x22;" value="undefined">
          Log message.
        </PyParameter>

        <PyParameter name="&#x22;level&#x22;" type="&#x22;str&#x22;" value="&#x22;'info'&#x22;">
          Log level (default: info).
        </PyParameter>

        <PyParameter name="&#x22;extra&#x22;" type="&#x22;Any&#x22;" value="&#x22;{}&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;">
        None
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;with_asset_logging&#x22;" type="&#x22;(func) -> Callable[..., T]&#x22;">
      Decorator to add automatic start/end logging with correlation fields.

      <PySourceCode>
        ```python
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
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;func&#x22;" type="&#x22;Callable[..., T]&#x22;" value="undefined">
          Function to wrap.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;typing.Callable&#x22;">
        Wrapped function with lifecycle logging.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
