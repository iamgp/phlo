# LogRouterHandler (/docs/python-reference/core/phlo/logging/LogRouterHandler)



Route log records to the hook bus as LogEvent payloads.

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, *, service_name, level=logging.NOTSET) -> None&#x22;">
  Initialize a router handler for hook-bus log forwarding.

  <PySourceCode>
    ```python
    def __init__(self, *, service_name: str, level: int = logging.NOTSET) -> None:
        """Initialize a router handler for hook-bus log forwarding.

        Args:
            service_name: Default service name for emitted log events.
            level: Minimum log level accepted by this handler.

        """
        super().__init__(level=level)
        self._service_name = service_name
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;service_name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Default service name for emitted log events.
    </PyParameter>

    <PyParameter name="&#x22;level&#x22;" type="&#x22;int&#x22;" value="&#x22;logging.NOTSET&#x22;">
      Minimum log level accepted by this handler.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;emit&#x22;" type="&#x22;(self, record) -> None&#x22;">
  Emit a log record to the hook bus as a structured log event.

  <PySourceCode>
    ```python
    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to the hook bus as a structured log event.

        Args:
            record: Standard library log record to route.

        """
        if _ROUTER_ACTIVE.get():
            return
        token = _ROUTER_ACTIVE.set(True)
        try:
            event = _record_to_event(record, self._service_name)
            if event is None:
                return
            from phlo.hooks.bus import get_hook_bus

            get_hook_bus().emit(event)
        except Exception:
            self.handleError(record)
        finally:
            _ROUTER_ACTIVE.reset(token)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;record&#x22;" type="&#x22;logging.LogRecord&#x22;" value="undefined">
      Standard library log record to route.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
