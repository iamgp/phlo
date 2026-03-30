# resource (/docs/python-reference/packages/phlo-trino/phlo_trino/resource)



Trino resource for executing queries and managing connections.

This module provides the TrinoResource class for interacting with Trino,
including connection management, query execution, and wait-for-readiness
functionality with automatic retry logic.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<PyAttribute name="&#x22;TRINO_QUERY_ENGINE_SUPPORT&#x22;" type="null" value="&#x22;CapabilitySupport(supports_refs=True, supports_time_travel=True)&#x22;" />

<PyAttribute name="&#x22;config&#x22;" type="null" value="&#x22;_ConfigFacade()&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;_ConfigFacade&#x22;" href="&#x22;/docs/python-reference/packages/phlo-trino/phlo_trino/resource/_ConfigFacade&#x22;" />

      <Card title="&#x22;TrinoResource&#x22;" href="&#x22;/docs/python-reference/packages/phlo-trino/phlo_trino/resource/TrinoResource&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_is_transient_trino_error&#x22;" type="&#x22;(exc) -> bool&#x22;">
      Check whether an exception chain indicates transient Trino startup/connectivity errors.

      <PySourceCode>
        ```python
        def _is_transient_trino_error(exc: Exception) -> bool:
            """Check whether an exception chain indicates transient Trino startup/connectivity errors.

            Args:
                exc: Root exception to inspect.

            Returns:
                True when retrying is likely useful; otherwise False.

            """
            for error in _iter_exception_chain(exc):
                message = str(error).lower()
                if "server_starting_up" in message:
                    return True
                if any(
                    snippet in message
                    for snippet in (
                        "connection refused",
                        "failed to establish",
                        "max retries exceeded",
                        "temporarily unavailable",
                        "connection reset",
                        "connection aborted",
                        "timed out",
                    )
                ):
                    return True
                errno = getattr(error, "errno", None)
                if errno in {104, 111, 113}:
                    return True
                error_code = getattr(error, "error_code", None)
                if error_code:
                    error_name = getattr(error_code, "name", None)
                    if error_name and "server_starting_up" in str(error_name).lower():
                        return True
                    error_value = getattr(error_code, "code", None)
                    if error_value and "server_starting_up" in str(error_value).lower():
                        return True
                error_name = getattr(error, "error_name", None)
                if error_name and "server_starting_up" in str(error_name).lower():
                    return True
                module_name = getattr(error.__class__, "__module__", "")
                class_name = error.__class__.__name__.lower()
                if module_name.startswith("urllib3") or module_name.startswith("requests"):
                    return True
                if "connectionerror" in class_name or "connection" in class_name:
                    return True
            return False
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;exc&#x22;" type="&#x22;Exception&#x22;" value="undefined">
          Root exception to inspect.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;bool&#x22;">
        True when retrying is likely useful; otherwise False.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_iter_exception_chain&#x22;" type="&#x22;(exc) -> Iterable[BaseException]&#x22;">
      Yield an exception and its chained causes/contexts.

      <PySourceCode>
        ```python
        def _iter_exception_chain(exc: BaseException) -> Iterable[BaseException]:
            """Yield an exception and its chained causes/contexts.

            Args:
                exc: Starting exception.

            Yields:
                Exception objects from the chain, root first.

            """
            current: BaseException | None = exc
            while current is not None:
                yield current
                current = current.__cause__ or current.__context__
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;exc&#x22;" type="&#x22;BaseException&#x22;" value="undefined">
          Starting exception.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;typing.Iterable[BaseException]&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
