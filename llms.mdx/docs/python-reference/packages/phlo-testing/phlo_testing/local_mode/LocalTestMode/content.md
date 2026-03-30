# LocalTestMode (/docs/python-reference/packages/phlo-testing/phlo_testing/local_mode/LocalTestMode)



Context manager to enable local test mode.

Replaces production resources with mocks for fast local testing.

Attributes [#attributes]

<PyAttribute name="&#x22;fixture_dir&#x22;" type="null" value="&#x22;fixture_dir or Path(tempfile.gettempdir()) / 'phlo_test_fixtures'&#x22;">
  Directory for fixture recording/playback.
</PyAttribute>

<PyAttribute name="&#x22;use_recorded_fixtures&#x22;" type="null" value="&#x22;use_recorded_fixtures&#x22;">
  Whether to use pre-recorded fixtures.
</PyAttribute>

<PyAttribute name="&#x22;_original_env&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;{}&#x22;" />

<PyAttribute name="&#x22;_fixtures&#x22;" type="&#x22;dict[str, Any]&#x22;" value="&#x22;{}&#x22;" />

<PyAttribute name="&#x22;table_store&#x22;" type="null" value="&#x22;MockIcebergCatalog()&#x22;">
  MockIcebergCatalog instance for table operations.
</PyAttribute>

<PyAttribute name="&#x22;trino&#x22;" type="null" value="&#x22;MockTrinoResource()&#x22;">
  MockTrinoResource instance for SQL execution.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, fixture_dir=None, use_recorded_fixtures=False) -> None&#x22;">
  Initialize local test mode.

  <PySourceCode>
    ```python
    def __init__(
        self,
        fixture_dir: Optional[Path] = None,
        use_recorded_fixtures: bool = False,
    ) -> None:
        """Initialize local test mode.

        Args:
            fixture_dir: Directory for fixture recording/playback.
            use_recorded_fixtures: Whether to use pre-recorded fixtures.

        """
        self.fixture_dir = fixture_dir or Path(tempfile.gettempdir()) / "phlo_test_fixtures"
        self.fixture_dir.mkdir(exist_ok=True)

        self.use_recorded_fixtures = use_recorded_fixtures
        self._original_env: dict[str, Any] = {}
        self._fixtures: dict[str, Any] = {}

        # Initialize mock resources
        self.table_store = MockIcebergCatalog()
        self.trino = MockTrinoResource()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;fixture_dir&#x22;" type="&#x22;Optional[Path]&#x22;" value="&#x22;None&#x22;">
      Directory for fixture recording/playback.
    </PyParameter>

    <PyParameter name="&#x22;use_recorded_fixtures&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;">
      Whether to use pre-recorded fixtures.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;__enter__&#x22;" type="&#x22;(self) -> 'LocalTestMode'&#x22;">
  Enter local test mode.

  Saves original environment and sets local test flags.

  <PySourceCode>
    ```python
    def __enter__(self) -> "LocalTestMode":
        """Enter local test mode.

        Saves original environment and sets local test flags.

        Returns:
            Self for context manager use.

        """
        # Save original environment
        self._original_env = os.environ.copy()

        # Set local test mode flag
        os.environ["PHLO_TEST_LOCAL"] = "1"
        os.environ["PHLO_LOG_LEVEL"] = "DEBUG"

        # Load recorded fixtures if available
        if self.use_recorded_fixtures:
            self._load_fixtures()

        return self
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;'LocalTestMode'&#x22;">
    Self for context manager use.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__exit__&#x22;" type="&#x22;(self, exc_type, exc_val, exc_tb) -> None&#x22;">
  Exit local test mode.

  Restores original environment and cleans up resources.

  <PySourceCode>
    ```python
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit local test mode.

        Restores original environment and cleans up resources.
        """
        # Restore original environment
        os.environ.clear()
        os.environ.update(self._original_env)

        # Clean up resources
        self.table_store.close()
        self.trino.close()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;exc_type&#x22;" type="&#x22;Any&#x22;" value="null" />

    <PyParameter name="&#x22;exc_val&#x22;" type="&#x22;Any&#x22;" value="null" />

    <PyParameter name="&#x22;exc_tb&#x22;" type="&#x22;Any&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;record_fixture&#x22;" type="&#x22;(self, name, data) -> None&#x22;">
  Record a fixture for later playback.

  <PySourceCode>
    ```python
    def record_fixture(self, name: str, data: Any) -> None:
        """Record a fixture for later playback.

        Args:
            name: Fixture name.
            data: Data to record.

        """
        fixture_file = self.fixture_dir / f"{name}.json"

        # Convert to JSON-serializable format
        if hasattr(data, "to_dict"):
            data = data.to_dict()
        elif hasattr(data, "to_json"):
            data = data.to_json()

        with open(fixture_file, "w") as f:
            json.dump(data, f, indent=2, default=str)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fixture name.
    </PyParameter>

    <PyParameter name="&#x22;data&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Data to record.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;load_fixture&#x22;" type="&#x22;(self, name) -> Any&#x22;">
  Load a recorded fixture.

  <PySourceCode>
    ```python
    def load_fixture(self, name: str) -> Any:
        """Load a recorded fixture.

        Args:
            name: Fixture name.

        Returns:
            Fixture data.

        Raises:
            FileNotFoundError: If fixture doesn't exist.

        """
        fixture_file = self.fixture_dir / f"{name}.json"

        if not fixture_file.exists():
            raise FileNotFoundError(f"Fixture not found: {fixture_file}")

        with open(fixture_file) as f:
            return json.load(f)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fixture name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    Fixture data.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_load_fixtures&#x22;" type="&#x22;(self) -> None&#x22;">
  Load all recorded fixtures.

  <PySourceCode>
    ```python
    def _load_fixtures(self) -> None:
        """Load all recorded fixtures."""
        if not self.fixture_dir.exists():
            return

        for fixture_file in self.fixture_dir.glob("*.json"):
            name = fixture_file.stem
            with open(fixture_file) as f:
                self._fixtures[name] = json.load(f)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;get_resource&#x22;" type="&#x22;(self, name) -> Any&#x22;">
  Get a mock resource.

  <PySourceCode>
    ```python
    def get_resource(self, name: str) -> Any:
        """Get a mock resource.

        Args:
            name: Resource name (table_store, trino).

        Returns:
            Mock resource.

        Raises:
            ValueError: If resource doesn't exist.

        """
        resources = {
            "table_store": self.table_store,
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
      Resource name (table\_store, trino).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;typing.Any&#x22;">
    Mock resource.
  </PyFunctionReturn>
</PyFunction>
