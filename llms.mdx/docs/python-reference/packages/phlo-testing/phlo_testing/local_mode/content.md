# local_mode (/docs/python-reference/packages/phlo-testing/phlo_testing/local_mode)



Local test mode for running tests without Docker.

Enables `phlo test --local` by automatically swapping production resources
with mock implementations backed by DuckDB.

Example:

> > > os.environ\["PHLO\_TEST\_LOCAL"] = "1"
> > >
> > > Assets automatically use mocks [#assets-automatically-use-mocks]

<PyAttribute name="&#x22;local_test&#x22;" type="null" value="&#x22;LocalTestDecorator()&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;LocalTestMode&#x22;" href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/local_mode/LocalTestMode&#x22;" />

      <Card title="&#x22;LocalTestDecorator&#x22;" href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/local_mode/LocalTestDecorator&#x22;" />

      <Card title="&#x22;FixtureRecorder&#x22;" href="&#x22;/docs/python-reference/packages/phlo-testing/phlo_testing/local_mode/FixtureRecorder&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;local_test_mode&#x22;" type="&#x22;(fixture_dir=None) -> Iterator['LocalTestMode']&#x22;">
      Context manager for local test mode.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        > > > with local\_test\_mode() as mode:
        > > > ...     # Test with mocked resources
        > > > ...     table = mode.table\_store.create\_table(...)
      </Callout>

      <PySourceCode>
        ```python
        @contextmanager
        def local_test_mode(
            fixture_dir: Optional[Path] = None,
        ) -> Iterator["LocalTestMode"]:
            """Context manager for local test mode.

            Args:
                fixture_dir: Directory for fixtures.

            Yields:
                LocalTestMode instance.

            Example:
                >>> with local_test_mode() as mode:
                ...     # Test with mocked resources
                ...     table = mode.table_store.create_table(...)

            """
            mode = LocalTestMode(fixture_dir=fixture_dir)

            with mode:
                yield mode
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;fixture_dir&#x22;" type="&#x22;Optional[Path]&#x22;" value="&#x22;None&#x22;">
          Directory for fixtures.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;typing.Iterator['LocalTestMode']&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;is_local_test_mode&#x22;" type="&#x22;() -> bool&#x22;">
      Check if running in local test mode.

      <PySourceCode>
        ```python
        def is_local_test_mode() -> bool:
            """Check if running in local test mode.

            Returns:
                True if PHLO_TEST_LOCAL environment variable is set.

            """
            return os.environ.get("PHLO_TEST_LOCAL", "").lower() in ("1", "true")
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;bool&#x22;">
        True if PHLO\_TEST\_LOCAL environment variable is set.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;enable_local_test_mode&#x22;" type="&#x22;() -> None&#x22;">
      Enable local test mode for current process.

      <PySourceCode>
        ```python
        def enable_local_test_mode() -> None:
            """Enable local test mode for current process."""
            os.environ["PHLO_TEST_LOCAL"] = "1"
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;disable_local_test_mode&#x22;" type="&#x22;() -> None&#x22;">
      Disable local test mode for current process.

      <PySourceCode>
        ```python
        def disable_local_test_mode() -> None:
            """Disable local test mode for current process."""
            os.environ.pop("PHLO_TEST_LOCAL", None)
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;set_fixture_dir&#x22;" type="&#x22;(path) -> None&#x22;">
      Set fixture directory path.

      <PySourceCode>
        ```python
        def set_fixture_dir(path: Path) -> None:
            """Set fixture directory path.

            Args:
                path: Path to fixture directory.

            """
            os.environ["PHLO_FIXTURE_DIR"] = str(path)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;path&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Path to fixture directory.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;get_fixture_dir&#x22;" type="&#x22;() -> Path&#x22;">
      Get fixture directory path.

      <PySourceCode>
        ```python
        def get_fixture_dir() -> Path:
            """Get fixture directory path.

            Returns:
                Path to fixture directory.

            """
            env_path = os.environ.get("PHLO_FIXTURE_DIR")

            if env_path:
                return Path(env_path)

            return Path(tempfile.gettempdir()) / "phlo_fixtures"
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;pathlib.Path&#x22;">
        Path to fixture directory.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
