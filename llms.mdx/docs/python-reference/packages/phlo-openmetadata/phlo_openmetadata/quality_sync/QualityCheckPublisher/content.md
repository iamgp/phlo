# QualityCheckPublisher (/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/quality_sync/QualityCheckPublisher)



Publishes quality check results to OpenMetadata.

Handles creating test definitions, cases, and publishing results.
Coordinates with OpenMetadataClient to sync quality metadata.

Attributes [#attributes]

<PyAttribute name="&#x22;om_client&#x22;" type="null" value="&#x22;om_client&#x22;">
  OpenMetadataClient instance for API operations.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, om_client)&#x22;">
  Initialize publisher with an OpenMetadata client.

  <PySourceCode>
    ```python
    def __init__(self, om_client: OpenMetadataClient):
        """Initialize publisher with an OpenMetadata client.

        Args:
            om_client: Client used to create definitions, cases, and results.

        """
        self.om_client = om_client
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;om_client&#x22;" type="&#x22;OpenMetadataClient&#x22;" value="undefined">
      Client used to create definitions, cases, and results.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;publish_test_definitions&#x22;" type="&#x22;(self, checks, table_fqn) -> dict[str, int]&#x22;">
  Publish quality check definitions to OpenMetadata.

  <PySourceCode>
    ```python
    def publish_test_definitions(
        self,
        checks: list[Any],
        table_fqn: str,
    ) -> dict[str, int]:
        """Publish quality check definitions to OpenMetadata.

        Args:
            checks: List of quality checks.
            table_fqn: Fully qualified table name.

        Returns:
            Dictionary with publication statistics.

        """
        # Pre-map all checks to avoid duplicate mapping
        mapped_defs = [
            (check, QualityCheckMapper.map_check_to_openmetadata_test_definition(check, table_fqn))
            for check in checks
        ]

        def publish(item: tuple[Any, dict[str, Any]]) -> None:
            """Create one OpenMetadata test definition from a mapped check."""
            _check, test_def = item
            self.om_client.create_test_definition(
                test_name=test_def["name"],
                test_type=test_def.get("testType"),
                description=test_def.get("description"),
                entity_type=test_def.get("entityType"),
                parameter_definition=test_def.get("parameterDefinition"),
                test_platforms=test_def.get("testPlatforms"),
            )

        def get_name(item: tuple[Any, dict[str, Any]]) -> str:
            """Return the definition name used for deduplication and reporting."""
            _check, test_def = item
            return test_def["name"]

        return _publish_items(mapped_defs, publish, get_name, "test definition")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;checks&#x22;" type="&#x22;list[Any]&#x22;" value="undefined">
      List of quality checks.
    </PyParameter>

    <PyParameter name="&#x22;table_fqn&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary with publication statistics.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;publish_test_cases&#x22;" type="&#x22;(self, checks, table_fqn, test_suite_name=None) -> dict[str, int]&#x22;">
  Publish quality check cases to OpenMetadata.

  <PySourceCode>
    ```python
    def publish_test_cases(
        self,
        checks: list[Any],
        table_fqn: str,
        test_suite_name: Optional[str] = None,
    ) -> dict[str, int]:
        """Publish quality check cases to OpenMetadata.

        Args:
            checks: List of quality checks.
            table_fqn: Fully qualified table name.
            test_suite_name: Optional test suite name.

        Returns:
            Dictionary with publication statistics.

        """
        # Pre-map all checks to avoid duplicate mapping
        mapped_cases = [
            (check, QualityCheckMapper.map_check_to_test_case(check, table_fqn, test_suite_name))
            for check in checks
        ]

        def publish(item: tuple[Any, dict[str, Any]]) -> None:
            """Create one OpenMetadata test case from a mapped check."""
            _check, test_case = item
            self.om_client.create_test_case(
                test_case_name=test_case["name"],
                table_fqn=table_fqn,
                test_definition_name=test_case["testDefinition"]["name"],
                parameters={p["name"]: p["value"] for p in test_case.get("parameterValues", [])},
                description=test_case.get("description"),
                entity_link=test_case.get("entityLink"),
                test_suite_name=test_case.get("testSuite", {}).get("name"),
            )

        def get_name(item: tuple[Any, dict[str, Any]]) -> str:
            """Return the test-case name used for deduplication and reporting."""
            _check, test_case = item
            return test_case["name"]

        return _publish_items(mapped_cases, publish, get_name, "test case")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;checks&#x22;" type="&#x22;list[Any]&#x22;" value="undefined">
      List of quality checks.
    </PyParameter>

    <PyParameter name="&#x22;table_fqn&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name.
    </PyParameter>

    <PyParameter name="&#x22;test_suite_name&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Optional test suite name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary with publication statistics.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;publish_test_results&#x22;" type="&#x22;(self, results) -> dict[str, int]&#x22;">
  Publish quality check results to OpenMetadata.

  <PySourceCode>
    ```python
    def publish_test_results(
        self,
        results: list[dict[str, Any]],
    ) -> dict[str, int]:
        """Publish quality check results to OpenMetadata.

        Args:
            results: List of test result dictionaries with
                     'test_case_fqn', 'check_result', and 'timestamp' keys.

        Returns:
            Dictionary with publication statistics.

        """
        stats = {"published": 0, "failed": 0}

        for result in results:
            try:
                test_case_fqn = result.get("test_case_fqn")
                check_result = result.get("check_result")
                timestamp = result.get("timestamp")

                if not test_case_fqn or not check_result:
                    logger.warning("invalid_test_result_skipped", result=result)
                    continue

                om_result = QualityCheckMapper.map_check_result_to_test_result(
                    check_result, test_case_fqn, timestamp
                )

                self.om_client.publish_test_result(
                    test_case_fqn=test_case_fqn,
                    result=om_result["result"],
                    test_execution_date=datetime.fromtimestamp(om_result["timestamp"] / 1000),
                    result_value=om_result.get("result_value"),
                )

                logger.info("test_result_published", test_case_fqn=test_case_fqn)
                stats["published"] += 1

            except Exception as exc:
                logger.error("test_result_publish_failed", error=str(exc))
                stats["failed"] += 1

        return stats
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;results&#x22;" type="&#x22;list[dict[str, Any]]&#x22;" value="undefined">
      List of test result dictionaries with
      'test\_case\_fqn', 'check\_result', and 'timestamp' keys.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary with publication statistics.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;publish_dbt_tests&#x22;" type="&#x22;(self, dbt_tests, table_fqn) -> dict[str, int]&#x22;">
  Publish dbt test definitions to OpenMetadata.

  <PySourceCode>
    ```python
    def publish_dbt_tests(
        self,
        dbt_tests: list[dict[str, Any]],
        table_fqn: str,
    ) -> dict[str, int]:
        """Publish dbt test definitions to OpenMetadata.

        Args:
            dbt_tests: List of dbt tests from manifest.
            table_fqn: Fully qualified table name.

        Returns:
            Dictionary with publication statistics.

        """
        # Pre-map all dbt tests to avoid duplicate mapping
        mapped_tests = [
            (dbt_test, QualityCheckMapper.map_dbt_test_to_openmetadata(dbt_test, table_fqn))
            for dbt_test in dbt_tests
        ]

        def publish(item: tuple[dict[str, Any], dict[str, Any]]) -> None:
            """Create one OpenMetadata test case from a mapped dbt test."""
            _dbt_test, test_case = item
            self.om_client.create_test_case(
                test_case_name=test_case["name"],
                table_fqn=table_fqn,
                test_definition_name=test_case["testDefinition"]["name"],
                parameters={p["name"]: p["value"] for p in test_case.get("parameterValues", [])},
                description=test_case.get("description"),
                entity_link=test_case.get("entityLink"),
                test_suite_name=test_case.get("testSuite", {}).get("name"),
            )

        def get_name(item: tuple[dict[str, Any], dict[str, Any]]) -> str:
            """Return the dbt-derived test-case name for deduplication."""
            _dbt_test, test_case = item
            return test_case["name"]

        return _publish_items(mapped_tests, publish, get_name, "dbt test case")
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;dbt_tests&#x22;" type="&#x22;list[dict[str, Any]]&#x22;" value="undefined">
      List of dbt tests from manifest.
    </PyParameter>

    <PyParameter name="&#x22;table_fqn&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary with publication statistics.
  </PyFunctionReturn>
</PyFunction>
