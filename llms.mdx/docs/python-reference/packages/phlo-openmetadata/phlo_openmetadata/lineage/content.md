# lineage (/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/lineage)



Lineage extraction and publishing for OpenMetadata.

Extracts lineage information from Dagster and dbt,
and publishes it to OpenMetadata for data discovery and impact analysis.

Example:

> > > from phlo\_openmetadata.lineage import LineageExtractor
> > > extractor = LineageExtractor()
> > > extractor.extract\_from\_dbt\_manifest(manifest\_dict)
> > > stats = extractor.publish\_to\_openmetadata(client)

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<PyAttribute name="&#x22;P&#x22;" type="null" value="&#x22;ParamSpec('P')&#x22;" />

<PyAttribute name="&#x22;R&#x22;" type="null" value="&#x22;TypeVar('R')&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;LineageExtractor&#x22;" href="&#x22;/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/lineage/LineageExtractor&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;log_extraction_errors&#x22;" type="&#x22;(source_name) -> Callable[[Callable[P, R]], Callable[P, R]]&#x22;">
      Decorator that logs exceptions with context and re-raises them.

      Wraps lineage extraction functions to provide consistent error logging
      with source identification.

      <PySourceCode>
        ```python
        def log_extraction_errors(source_name: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
            """Decorator that logs exceptions with context and re-raises them.

            Wraps lineage extraction functions to provide consistent error logging
            with source identification.

            Args:
                source_name: Identifier for the lineage source (e.g., 'Dagster', 'dbt').

            Returns:
                Callable[[Callable[P, R]], Callable[P, R]]: Decorator function that
                    adds error logging.

            """

            def decorator(fn: Callable[P, R]) -> Callable[P, R]:
                """Wrap an extraction function with source-aware error logging.

                Args:
                    fn: Extraction function to wrap.

                Returns:
                    Callable[P, R]: Wrapped function that logs failures with source context.

                """

                @wraps(fn)
                def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
                    """Execute extraction function and log source-specific failures.

                    Args:
                        *args: Positional arguments forwarded to the wrapped callable.
                        **kwargs: Keyword arguments forwarded to the wrapped callable.

                    Returns:
                        R: Result produced by the wrapped callable.

                    Raises:
                        Exception: Re-raises any exception after logging.

                    """
                    try:
                        return fn(*args, **kwargs)
                    except Exception as exc:
                        logger.error(
                            "lineage_extraction_failed",
                            source=source_name,
                            error=str(exc),
                        )
                        raise

                return wrapper

            return decorator
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;source_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Identifier for the lineage source (e.g., 'Dagster', 'dbt').
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;typing.Callable&#x22;">
        Callable\[\[Callable\[P, R]], Callable\[P, R]]: Decorator function that
        adds error logging.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
