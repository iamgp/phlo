# MockAssetContext (/docs/python-reference/packages/phlo-testing/phlo_testing/execution/MockAssetContext)



Mock Dagster context for asset execution.

Provides mocked resources (Iceberg, Trino, DLT) and logging capabilities
for testing assets without requiring a full Dagster environment.

Attributes [#attributes]

<PyAttribute name="&#x22;partition_key&#x22;" type="null" value="&#x22;partition_key or '2024-01-01'&#x22;">
  Partition identifier (e.g., "2024-01-01").
</PyAttribute>

<PyAttribute name="&#x22;iceberg&#x22;" type="null" value="&#x22;mock_iceberg or MockIcebergCatalog()&#x22;">
  MockIcebergCatalog instance for table operations.
</PyAttribute>

<PyAttribute name="&#x22;trino&#x22;" type="null" value="&#x22;mock_trino or MockTrinoResource()&#x22;">
  MockTrinoResource instance for SQL execution.
</PyAttribute>

<PyAttribute name="&#x22;_logs&#x22;" type="&#x22;list[str]&#x22;" value="&#x22;[]&#x22;" />

<PyAttribute name="&#x22;_logger&#x22;" type="null" value="&#x22;self._create_logger()&#x22;" />

<PyAttribute name="&#x22;logs&#x22;" type="&#x22;list[str]&#x22;" value="null">
  Get all captured logs.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, partition_key=None, mock_iceberg=None, mock_trino=None) -> None&#x22;">
  Initialize mock context.

  <PySourceCode>
    ```python
    def __init__(
        self,
        partition_key: Optional[str] = None,
        mock_iceberg: Optional[MockIcebergCatalog] = None,
        mock_trino: Optional[MockTrinoResource] = None,
    ) -> None:
        """Initialize mock context.

        Args:
            partition_key: Partition identifier (e.g., "2024-01-01").
            mock_iceberg: MockIcebergCatalog instance (creates new if None).
            mock_trino: MockTrinoResource instance (creates new if None).

        """
        self.partition_key = partition_key or "2024-01-01"
        self.iceberg = mock_iceberg or MockIcebergCatalog()
        self.trino = mock_trino or MockTrinoResource()

        self._logs: list[str] = []
        self._logger = self._create_logger()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;partition_key&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Partition identifier (e.g., "2024-01-01").
    </PyParameter>

    <PyParameter name="&#x22;mock_iceberg&#x22;" type="&#x22;Optional[MockIcebergCatalog]&#x22;" value="&#x22;None&#x22;">
      MockIcebergCatalog instance (creates new if None).
    </PyParameter>

    <PyParameter name="&#x22;mock_trino&#x22;" type="&#x22;Optional[MockTrinoResource]&#x22;" value="&#x22;None&#x22;">
      MockTrinoResource instance (creates new if None).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_create_logger&#x22;" type="&#x22;(self) -> Any&#x22;">
  Create logger that captures to self.\_logs.

  <PySourceCode>
    ```python
    def _create_logger(self) -> Any:
        """Create logger that captures to self._logs.

        Returns:
            Logger instance with capture handler attached.

        """
        name = f"asset_test_{id(self)}"
        logger = get_logger(name)

        std_logger = logging.getLogger(name)
        std_logger.setLevel(logging.DEBUG)
        std_logger.propagate = False
        std_logger.handlers = []

        # Add custom handler to capture logs
        class LogCapture(logging.Handler):
            """Logging handler that appends formatted records to a list."""

            def __init__(self, logs_list: list[str]) -> None:
                """Initialize the capture handler.

                Args:
                    logs_list: Destination list for formatted log messages.

                """
                super().__init__()
                self.logs = logs_list

            def emit(self, record: logging.LogRecord) -> None:
                """Store a formatted log record.

                Args:
                    record: Log record emitted by the logger.

                """
                self.logs.append(self.format(record))

        handler = LogCapture(self._logs)
        formatter = logging.Formatter(
            "%(levelname)s - %(name)s - %(message)s",
        )
        handler.setFormatter(formatter)
        std_logger.addHandler(handler)

        return logger
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    Logger instance with capture handler attached.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;log&#x22;" type="&#x22;(self, message, level='INFO') -> None&#x22;">
  Log a message.

  <PySourceCode>
    ```python
    def log(self, message: str, level: str = "INFO") -> None:
        """Log a message.

        Args:
            message: Message to log.
            level: Log level (DEBUG, INFO, WARNING, ERROR).

        """
        resolved_level = level.lower()
        if resolved_level == "warn":
            resolved_level = "warning"
        getattr(self._logger, resolved_level)(message)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;message&#x22;" type="&#x22;str&#x22;" value="undefined">
      Message to log.
    </PyParameter>

    <PyParameter name="&#x22;level&#x22;" type="&#x22;str&#x22;" value="&#x22;'INFO'&#x22;">
      Log level (DEBUG, INFO, WARNING, ERROR).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_resource&#x22;" type="&#x22;(self, name) -> Any&#x22;">
  Get a mock resource by name.

  <PySourceCode>
    ```python
    def get_resource(self, name: str) -> Any:
        """Get a mock resource by name.

        Args:
            name: Resource name (table_store, trino, etc.).

        Returns:
            Mock resource instance.

        Raises:
            ValueError: If resource doesn't exist.

        """
        resources = {
            "table_store": self.iceberg,
            "trino": self.trino,
        }

        if name not in resources:
            raise ValueError(f"Unknown resource: {name}")

        return resources[name]
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Resource name (table\_store, trino, etc.).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    Mock resource instance.
  </PyFunctionReturn>
</PyFunction>
