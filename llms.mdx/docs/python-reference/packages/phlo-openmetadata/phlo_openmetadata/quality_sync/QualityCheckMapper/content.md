# QualityCheckMapper (/docs/python-reference/packages/phlo-openmetadata/phlo_openmetadata/quality_sync/QualityCheckMapper)



Maps quality checks to OpenMetadata test definitions.

Converts @phlo\_quality checks to OpenMetadata TestDefinition objects
and handles parameter mapping for various check types including:

* NullCheck: Column null value validation
* RangeCheck: Numeric range validation
* UniqueCheck: Column uniqueness validation
* CountCheck: Row count validation
* FreshnessCheck: Data recency validation
* CustomSQLCheck: Custom SQL-based validation

Attributes [#attributes]

<PyAttribute name="&#x22;CHECK_TYPE_MAP&#x22;" type="null" value="&#x22;{'NullCheck': 'nullCheck', 'RangeCheck': 'rangeCheck', 'UniqueCheck': 'uniqueCheck', 'CountCheck': 'countCheck', 'FreshnessCheck': 'freshnessCheck', 'SchemaCheck': 'schemaCheck', 'CustomSQLCheck': 'customSQLCheck'}&#x22;">
  Mapping of Phlo check types to OpenMetadata test types.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;map_check_to_openmetadata_test_definition&#x22;" type="&#x22;(cls, check, table_fqn) -> dict[str, Any]&#x22;">
  Convert quality check to OpenMetadata test definition format.

  <PySourceCode>
    ```python
    @classmethod
    def map_check_to_openmetadata_test_definition(
        cls,
        check: Any,  # Union of quality check classes
        table_fqn: str,
    ) -> dict[str, Any]:
        """Convert quality check to OpenMetadata test definition format.

        Args:
            check: Quality check instance.
            table_fqn: Fully qualified name of table being tested.

        Returns:
            Dictionary with test definition format.

        """
        check_type = type(check).__name__
        om_test_type = cls.CHECK_TYPE_MAP.get(check_type, "customCheck")

        # Get human-readable test name
        test_name = cls._get_test_name(check)

        return {
            "name": test_name,
            "displayName": test_name,
            "description": cls._get_test_description(check),
            "entityType": cls._get_entity_type(check),
            "parameterDefinition": cls._get_parameter_definition(check),
            "testPlatforms": ["OpenMetadata"],
            "testType": om_test_type,
        }
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;cls&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;check&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Quality check instance.
    </PyParameter>

    <PyParameter name="&#x22;table_fqn&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified name of table being tested.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary with test definition format.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;map_check_to_test_case&#x22;" type="&#x22;(cls, check, table_fqn, test_suite_name=None) -> dict[str, Any]&#x22;">
  Convert quality check to OpenMetadata test case format.

  <PySourceCode>
    ```python
    @classmethod
    def map_check_to_test_case(
        cls,
        check: Any,
        table_fqn: str,
        test_suite_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """Convert quality check to OpenMetadata test case format.

        Args:
            check: Quality check instance.
            table_fqn: Fully qualified name of table being tested.
            test_suite_name: Optional name for test suite.

        Returns:
            Dictionary with test case format.

        """
        test_name = cls._get_test_name(check)

        if not test_suite_name:
            # Create suite name from table name
            table_name = table_fqn.split(".")[-1]
            test_suite_name = f"{table_name}_quality_suite"

        test_suite_name = cls._sanitize_name(test_suite_name)
        test_case_name = f"{cls._sanitize_name(table_fqn)}_{cls._sanitize_name(test_name)}"

        return {
            "name": test_case_name,
            "entityLink": cls._get_entity_link(check, table_fqn),
            "testDefinition": {
                "name": cls._sanitize_name(test_name),
                "type": "testDefinition",
            },
            "testSuite": {
                "name": test_suite_name,
                "type": "testSuite",
            },
            "parameterValues": cls._get_parameter_values(check),
            "description": cls._get_test_description(check),
        }
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;cls&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;check&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Quality check instance.
    </PyParameter>

    <PyParameter name="&#x22;table_fqn&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified name of table being tested.
    </PyParameter>

    <PyParameter name="&#x22;test_suite_name&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
      Optional name for test suite.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary with test case format.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;map_check_result_to_test_result&#x22;" type="&#x22;(cls, check_result, test_case_fqn, execution_timestamp=None) -> dict[str, Any]&#x22;">
  Convert quality check result to OpenMetadata test result format.

  <PySourceCode>
    ```python
    @classmethod
    def map_check_result_to_test_result(
        cls,
        check_result: QualityCheckResult,
        test_case_fqn: str,
        execution_timestamp: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """Convert quality check result to OpenMetadata test result format.

        Args:
            check_result: QualityCheckResult from executing a check.
            test_case_fqn: Fully qualified name of test case.
            execution_timestamp: When the test executed.

        Returns:
            Dictionary with test result format.

        """
        if execution_timestamp is None:
            execution_timestamp = datetime.now(timezone.utc)

        return {
            "result": "Success" if check_result.passed else "Failed",
            "testCaseStatus": "Success" if check_result.passed else "Failed",
            "timestamp": int(execution_timestamp.timestamp() * 1000),
            "result_value": str(check_result.metric_value),
            "failureDetails": {
                "testFailureMessage": check_result.failure_message,
                "testFailureMetadata": json.dumps(check_result.metadata),
            }
            if not check_result.passed
            else None,
        }
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;cls&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;check_result&#x22;" type="&#x22;QualityCheckResult&#x22;" value="undefined">
      QualityCheckResult from executing a check.
    </PyParameter>

    <PyParameter name="&#x22;test_case_fqn&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified name of test case.
    </PyParameter>

    <PyParameter name="&#x22;execution_timestamp&#x22;" type="&#x22;Optional[datetime]&#x22;" value="&#x22;None&#x22;">
      When the test executed.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary with test result format.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;map_dbt_test_to_openmetadata&#x22;" type="&#x22;(cls, dbt_test, table_fqn) -> dict[str, Any]&#x22;">
  Convert dbt test to OpenMetadata test case format.

  <PySourceCode>
    ```python
    @classmethod
    def map_dbt_test_to_openmetadata(
        cls,
        dbt_test: dict[str, Any],
        table_fqn: str,
    ) -> dict[str, Any]:
        """Convert dbt test to OpenMetadata test case format.

        Args:
            dbt_test: dbt test metadata from manifest.
            table_fqn: Fully qualified name of table being tested.

        Returns:
            Dictionary with test case format.

        """
        test_name = dbt_test.get("name", "unknown_test")
        test_type = (
            dbt_test.get("type") or dbt_test.get("test_metadata", {}).get("name") or "unknown"
        )

        test_def_name = cls._sanitize_name(f"dbt_{test_type}")

        return {
            "name": f"{cls._sanitize_name(table_fqn)}_dbt_{cls._sanitize_name(test_name)}",
            "entityLink": cls._build_entity_link(table_fqn, None),
            "testDefinition": {
                "name": test_def_name,
                "type": "testDefinition",
            },
            "testSuite": {
                "name": cls._sanitize_name(f"{table_fqn.split('.')[-1]}_dbt_suite"),
                "type": "testSuite",
            },
            "parameterValues": cls._get_dbt_test_parameters(dbt_test),
            "description": dbt_test.get("description"),
        }
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;cls&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;dbt_test&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      dbt test metadata from manifest.
    </PyParameter>

    <PyParameter name="&#x22;table_fqn&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified name of table being tested.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary with test case format.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_get_test_name&#x22;" type="&#x22;(check) -> str&#x22;">
  Generate OpenMetadata-friendly test name from check.

  <PySourceCode>
    ```python
    @staticmethod
    def _get_test_name(check: Any) -> str:
        """Generate OpenMetadata-friendly test name from check.

        Args:
            check: Quality check instance.

        Returns:
            Sanitized test name string.

        """
        if isinstance(check, NullCheck):
            cols = "_".join(check.columns)
            return QualityCheckMapper._sanitize_name(f"null_check_{cols}")
        if isinstance(check, RangeCheck):
            return QualityCheckMapper._sanitize_name(f"range_check_{check.column}")
        if isinstance(check, UniqueCheck):
            cols = "_".join(check.columns)
            return QualityCheckMapper._sanitize_name(f"unique_check_{cols}")
        if isinstance(check, CountCheck):
            return "count_check"
        if isinstance(check, FreshnessCheck):
            return QualityCheckMapper._sanitize_name(f"freshness_check_{check.timestamp_column}")
        if isinstance(check, CustomSQLCheck):
            return QualityCheckMapper._sanitize_name(check.name_)
        return QualityCheckMapper._sanitize_name(type(check).__name__.lower())
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;check&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Quality check instance.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Sanitized test name string.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_sanitize_name&#x22;" type="&#x22;(value) -> str&#x22;">
  Sanitize entity names for OpenMetadata compatibility.

  <PySourceCode>
    ```python
    @staticmethod
    def _sanitize_name(value: str) -> str:
        """Sanitize entity names for OpenMetadata compatibility.

        Args:
            value: Raw entity name.

        Returns:
            Name with only alphanumeric and underscore characters.

        """
        cleaned = re.sub(r"[^A-Za-z0-9_]", "_", value).strip("_")
        return cleaned or "phlo"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;value&#x22;" type="&#x22;str&#x22;" value="undefined">
      Raw entity name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Name with only alphanumeric and underscore characters.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_build_entity_link&#x22;" type="&#x22;(table_fqn, column) -> str&#x22;">
  Build an OpenMetadata entity link for a table or table column.

  <PySourceCode>
    ```python
    @staticmethod
    def _build_entity_link(table_fqn: str, column: str | None) -> str:
        """Build an OpenMetadata entity link for a table or table column.

        Args:
            table_fqn: Fully qualified table name.
            column: Optional column name to target column-level links.

        Returns:
            OpenMetadata entity link string.

        """
        if column:
            return f"<#E::table::{table_fqn}::columns::{column}>"
        return f"<#E::table::{table_fqn}>"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;table_fqn&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name.
    </PyParameter>

    <PyParameter name="&#x22;column&#x22;" type="&#x22;str | None&#x22;" value="undefined">
      Optional column name to target column-level links.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    OpenMetadata entity link string.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_get_entity_link&#x22;" type="&#x22;(cls, check, table_fqn) -> str&#x22;">
  Build an entity link for the check scope.

  <PySourceCode>
    ```python
    @classmethod
    def _get_entity_link(cls, check: Any, table_fqn: str) -> str:
        """Build an entity link for the check scope.

        Args:
            check: Quality check instance.
            table_fqn: Fully qualified table name.

        Returns:
            OpenMetadata entity link for table or column scope.

        """
        column: str | None = None
        if isinstance(check, NullCheck) and len(check.columns) == 1:
            column = check.columns[0]
        elif isinstance(check, RangeCheck):
            column = check.column
        elif isinstance(check, FreshnessCheck):
            column = check.timestamp_column
        elif isinstance(check, UniqueCheck) and len(check.columns) == 1:
            column = check.columns[0]
        return cls._build_entity_link(table_fqn, column)
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;cls&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;check&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Quality check instance.
    </PyParameter>

    <PyParameter name="&#x22;table_fqn&#x22;" type="&#x22;str&#x22;" value="undefined">
      Fully qualified table name.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    OpenMetadata entity link for table or column scope.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_get_entity_type&#x22;" type="&#x22;(check) -> str&#x22;">
  Determine the OpenMetadata entity type for a check.

  <PySourceCode>
    ```python
    @staticmethod
    def _get_entity_type(check: Any) -> str:
        """Determine the OpenMetadata entity type for a check.

        Args:
            check: Quality check instance.

        Returns:
            'COLUMN' for column-scoped checks, otherwise 'TABLE'.

        """
        if isinstance(check, (NullCheck, RangeCheck, FreshnessCheck)):
            return "COLUMN"
        if isinstance(check, UniqueCheck) and len(check.columns) == 1:
            return "COLUMN"
        return "TABLE"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;check&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Quality check instance.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    'COLUMN' for column-scoped checks, otherwise 'TABLE'.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_get_test_description&#x22;" type="&#x22;(check) -> str&#x22;">
  Generate human-readable description for a quality check.

  <PySourceCode>
    ```python
    @staticmethod
    def _get_test_description(check: Any) -> str:
        """Generate human-readable description for a quality check.

        Args:
            check: Quality check instance.

        Returns:
            Description string explaining the check purpose.

        """
        if isinstance(check, NullCheck):
            return f"Check that columns {', '.join(check.columns)} have no null values"
        if isinstance(check, RangeCheck):
            return (
                f"Check that column {check.column} values are between "
                f"{check.min_value} and {check.max_value}"
            )
        if isinstance(check, UniqueCheck):
            return f"Check that columns {', '.join(check.columns)} values are unique"
        if isinstance(check, CountCheck):
            return f"Check that row count is between {check.min_rows} and {check.max_rows}"
        if isinstance(check, FreshnessCheck):
            return (
                f"Check that data is not older than {check.max_age_hours} hours based on "
                f"{check.timestamp_column}"
            )
        if isinstance(check, CustomSQLCheck):
            return f"Custom SQL quality check: {check.name_}"
        return "Quality check"
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;check&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Quality check instance.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;str&#x22;">
    Description string explaining the check purpose.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_get_parameter_definition&#x22;" type="&#x22;(check) -> list[dict[str, Any]]&#x22;">
  Extract parameter definitions for check type.

  <PySourceCode>
    ```python
    @staticmethod
    def _get_parameter_definition(check: Any) -> list[dict[str, Any]]:
        """Extract parameter definitions for check type.

        Args:
            check: Quality check instance.

        Returns:
            List of parameter definition dicts with name, dataType, and required.

        """
        if isinstance(check, NullCheck):
            return [
                {"name": "columns", "dataType": "STRING", "required": True},
                {"name": "allow_threshold", "dataType": "NUMBER", "required": False},
            ]
        if isinstance(check, RangeCheck):
            return [
                {"name": "column", "dataType": "STRING", "required": True},
                {"name": "min_value", "dataType": "NUMBER", "required": False},
                {"name": "max_value", "dataType": "NUMBER", "required": False},
            ]
        if isinstance(check, UniqueCheck):
            return [
                {"name": "columns", "dataType": "STRING", "required": True},
            ]
        if isinstance(check, CountCheck):
            return [
                {"name": "min_rows", "dataType": "NUMBER", "required": False},
                {"name": "max_rows", "dataType": "NUMBER", "required": False},
            ]
        if isinstance(check, FreshnessCheck):
            return [
                {"name": "timestamp_column", "dataType": "STRING", "required": True},
                {"name": "max_age_hours", "dataType": "NUMBER", "required": True},
            ]
        if isinstance(check, CustomSQLCheck):
            return [
                {"name": "sql", "dataType": "STRING", "required": True},
            ]
        return []
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;check&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Quality check instance.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of parameter definition dicts with name, dataType, and required.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_get_parameter_values&#x22;" type="&#x22;(check) -> list[dict[str, str]]&#x22;">
  Extract parameter values from a check instance.

  <PySourceCode>
    ```python
    @staticmethod
    def _get_parameter_values(check: Any) -> list[dict[str, str]]:
        """Extract parameter values from a check instance.

        Args:
            check: Quality check instance.

        Returns:
            List of parameter value dicts with name and value.

        """
        params: list[dict[str, str]] = []

        if isinstance(check, NullCheck):
            params.append({"name": "columns", "value": ",".join(check.columns)})
            params.append({"name": "allow_threshold", "value": str(check.allow_threshold)})
        elif isinstance(check, RangeCheck):
            params.append({"name": "column", "value": check.column})
            params.append({"name": "min_value", "value": str(check.min_value)})
            params.append({"name": "max_value", "value": str(check.max_value)})
        elif isinstance(check, UniqueCheck):
            params.append({"name": "columns", "value": ",".join(check.columns)})
        elif isinstance(check, CountCheck):
            if check.min_rows is not None:
                params.append({"name": "min_rows", "value": str(check.min_rows)})
            if check.max_rows is not None:
                params.append({"name": "max_rows", "value": str(check.max_rows)})
        elif isinstance(check, FreshnessCheck):
            params.append({"name": "timestamp_column", "value": check.timestamp_column})
            params.append({"name": "max_age_hours", "value": str(check.max_age_hours)})
        elif isinstance(check, CustomSQLCheck):
            params.append({"name": "sql", "value": check.sql})

        return params
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;check&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Quality check instance.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of parameter value dicts with name and value.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;_get_dbt_test_parameters&#x22;" type="&#x22;(dbt_test) -> list[dict[str, str]]&#x22;">
  Extract parameter values from dbt test metadata.

  <PySourceCode>
    ```python
    @staticmethod
    def _get_dbt_test_parameters(dbt_test: dict[str, Any]) -> list[dict[str, str]]:
        """Extract parameter values from dbt test metadata.

        Args:
            dbt_test: dbt test metadata dictionary.

        Returns:
            List of parameter value dicts.

        """
        params: list[dict[str, str]] = []
        kwargs = dbt_test.get("kwargs") or dbt_test.get("test_metadata", {}).get("kwargs", {})

        for key, value in kwargs.items():
            params.append({"name": key, "value": str(value)})

        return params
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;dbt_test&#x22;" type="&#x22;dict[str, Any]&#x22;" value="undefined">
      dbt test metadata dictionary.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;list&#x22;">
    List of parameter value dicts.
  </PyFunctionReturn>
</PyFunction>
