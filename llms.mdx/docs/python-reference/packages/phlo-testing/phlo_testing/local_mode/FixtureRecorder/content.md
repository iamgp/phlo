# FixtureRecorder (/docs/python-reference/packages/phlo-testing/phlo_testing/local_mode/FixtureRecorder)



Helper to record fixtures from real services.

Captures responses from production services and saves them for
replay in local mode.

Attributes [#attributes]

<PyAttribute name="&#x22;fixture_dir&#x22;" type="null" value="&#x22;fixture_dir or Path(tempfile.gettempdir()) / 'phlo_fixtures'&#x22;">
  Directory to store fixtures.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, fixture_dir=None) -> None&#x22;">
  Initialize recorder.

  <PySourceCode>
    ```python
    def __init__(self, fixture_dir: Optional[Path] = None) -> None:
        """Initialize recorder.

        Args:
            fixture_dir: Directory to store fixtures.

        """
        self.fixture_dir = fixture_dir or Path(tempfile.gettempdir()) / "phlo_fixtures"
        self.fixture_dir.mkdir(exist_ok=True)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;fixture_dir&#x22;" type="&#x22;Optional[Path]&#x22;" value="&#x22;None&#x22;">
      Directory to store fixtures.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>

<PyFunction name="&#x22;record_dlt_source&#x22;" type="&#x22;(self, name, source_func, *args, **kwargs) -> list[dict[str, Any]]&#x22;">
  Record data from a DLT source.

  <PySourceCode>
    ```python
    def record_dlt_source(
        self,
        name: str,
        source_func: Any,
        *args: Any,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Record data from a DLT source.

        Args:
            name: Fixture name.
            source_func: Function that returns DLT source.
            *args: Args to pass to source_func.
            **kwargs: Kwargs to pass to source_func.

        Returns:
            List of records from source.

        """
        # Call source function to get data
        source = source_func(*args, **kwargs)
        data = list(source)

        # Save to fixture
        fixture_file = self.fixture_dir / f"{name}_dlt.json"

        with open(fixture_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

        return data
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fixture name.
    </PyParameter>

    <PyParameter name="&#x22;source_func&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Function that returns DLT source.
    </PyParameter>

    <PyParameter name="&#x22;args&#x22;" type="&#x22;Any&#x22;" value="&#x22;()&#x22;" />

    <PyParameter name="&#x22;kwargs&#x22;" type="&#x22;Any&#x22;" value="&#x22;{}&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of records from source.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;record_sql_query&#x22;" type="&#x22;(self, name, query_func, *args, **kwargs) -> list[dict[str, Any]]&#x22;">
  Record results from a SQL query.

  <PySourceCode>
    ```python
    def record_sql_query(
        self,
        name: str,
        query_func: Any,
        *args: Any,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Record results from a SQL query.

        Args:
            name: Fixture name.
            query_func: Function that executes query.
            *args: Args to pass to query_func.
            **kwargs: Kwargs to pass to query_func.

        Returns:
            Query results.

        """
        # Execute query
        results = query_func(*args, **kwargs)

        # Convert to list of dicts if needed
        if hasattr(results, "to_dict"):
            data = results.to_dict("records")
        else:
            data = list(results)

        # Save to fixture
        fixture_file = self.fixture_dir / f"{name}_sql.json"

        with open(fixture_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

        return data
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fixture name.
    </PyParameter>

    <PyParameter name="&#x22;query_func&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Function that executes query.
    </PyParameter>

    <PyParameter name="&#x22;args&#x22;" type="&#x22;Any&#x22;" value="&#x22;()&#x22;" />

    <PyParameter name="&#x22;kwargs&#x22;" type="&#x22;Any&#x22;" value="&#x22;{}&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    Query results.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;load_dlt_fixture&#x22;" type="&#x22;(self, name) -> MockDLTResource&#x22;">
  Load a recorded DLT fixture.

  <PySourceCode>
    ```python
    def load_dlt_fixture(self, name: str) -> MockDLTResource:
        """Load a recorded DLT fixture.

        Args:
            name: Fixture name.

        Returns:
            MockDLTResource with recorded data.

        """
        fixture_file = self.fixture_dir / f"{name}_dlt.json"

        if not fixture_file.exists():
            raise FileNotFoundError(f"Fixture not found: {fixture_file}")

        with open(fixture_file) as f:
            data = json.load(f)

        return mock_dlt_source(data, resource_name=name)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fixture name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo_testing.mock_dlt.MockDLTResource&#x22;">
    MockDLTResource with recorded data.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;get_fixture_dir&#x22;" type="&#x22;(self) -> Path&#x22;">
  Get fixture directory path.

  <PySourceCode>
    ```python
    def get_fixture_dir(self) -> Path:
        """Get fixture directory path.

        Returns:
            Path to fixture directory.

        """
        return self.fixture_dir
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;pathlib.Path&#x22;">
    Path to fixture directory.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;list_fixtures&#x22;" type="&#x22;(self) -> list[str]&#x22;">
  List all recorded fixtures.

  <PySourceCode>
    ```python
    def list_fixtures(self) -> list[str]:
        """List all recorded fixtures.

        Returns:
            List of fixture names.

        """
        if not self.fixture_dir.exists():
            return []

        return sorted(f.stem for f in self.fixture_dir.glob("*.*"))
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of fixture names.
  </PyFunctionReturn>
</PyFunction>
