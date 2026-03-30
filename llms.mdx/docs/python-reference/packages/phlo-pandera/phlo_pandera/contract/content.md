# contract (/docs/python-reference/packages/phlo-pandera/phlo_pandera/contract)



Quality check naming and metadata contract.

This module defines a contract for asset check metadata so downstream consumers
(e.g., Observatory UI) can render results consistently without special-casing
check implementations. The contract standardizes naming conventions, severity
policies, partition semantics, and metadata keys across different check types
(Pandera, dbt, and Phlo native checks).

Contract Overview:

Naming Convention:

* Pandera schema contract check name: `pandera_contract`
* dbt test check name: `dbt__\<test_type>__\<target>`
* Quality check names are derived from the check class or user-provided name

Severity Policy:

* Pandera schema contract checks are blocking and emit ERROR on failure
* dbt tests default to ERROR for `not_null`, `unique`, `relationships`
* Other dbt test types default to WARN
* dbt tag overrides:
  * `tag:blocking` forces ERROR severity
  * `tag:warn` or `tag:anomaly` forces WARN severity

Partition Semantics:

* If a Dagster run provides a partition key, checks are scoped to that
  partition by default
* Default partition column: `_phlo_partition_date` (YYYY-MM-DD format)
* Override per-check via `partition_column` parameter
* Unpartitioned checks may use rolling window via `rolling_window_days`
* Set `full_table=True` to explicitly run without partition scoping

Required Metadata Keys:

* `source`: Check source type (`pandera`, `dbt`, `phlo`)
* `partition_key`: Partition key string when applicable
* `failed_count`: Number of failures (schema errors, failed tests, etc.)
* `total_count`: Total evaluated (rows, tests run, etc.) when available
* `query_or_sql`: SQL/query/command string used for evaluation
* `sample`: List of up to 20 sample rows/ids/errors when available

Optional Metadata Keys:

* `repro_sql`: Safe SQL snippet for reproducing failures in Trino
  (e.g., with LIMIT clause added)

Example:

```python
from phlo_pandera.contract import QualityCheckContract

contract = QualityCheckContract(
    source="pandera",
    failed_count=5,
    total_count=1000,
    partition_key="2024-01-15",
    query_or_sql="SELECT * FROM bronze.events WHERE _phlo_partition_date = '2024-01-15'",
    sample=[\{"row_index": 42, "error": "type mismatch"\}],
)

metadata = contract.to_metadata()
# Returns dict with standardized keys
```

See Also:

* `severity.py`: Severity mapping functions
* `decorator.py`: `@phlo_pandera` decorator that produces these contracts
* `pandera_asset_checks.py`: Pandera contract evaluation

<PyAttribute name="&#x22;PANDERA_CONTRACT_CHECK_NAME&#x22;" type="null" value="&#x22;'pandera_contract'&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;QualityCheckContract&#x22;" href="&#x22;/docs/python-reference/packages/phlo-pandera/phlo_pandera/contract/QualityCheckContract&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;dbt_check_name&#x22;" type="&#x22;(test_type, target) -> str&#x22;">
      Build a canonical Dagster-safe check name for a dbt test.

      Constructs check names in the format `dbt__\<test_type>__\<target>`,
      sanitizing the components to ensure compatibility with Dagster's naming
      constraints.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        dbt_check_name("not_null", "orders.id")
        # Returns: "dbt__not_null__orders_id"

        dbt_check_name("accepted_values", "orders.status")
        # Returns: "dbt__accepted_values__orders_status"
        ```
      </Callout>

      <PySourceCode>
        ````python
        def dbt_check_name(test_type: str, target: str) -> str:
            """Build a canonical Dagster-safe check name for a dbt test.

            Constructs check names in the format ``dbt__<test_type>__<target>``,
            sanitizing the components to ensure compatibility with Dagster's naming
            constraints.

            Args:
                test_type: dbt test type (e.g., ``not_null``, ``unique``, ``accepted_values``).
                target: Target model/column identifier for the test (e.g., ``orders.status``).

            Returns:
                Canonical check name in ``dbt__<test_type>__<target>`` format,
                with special characters replaced for Dagster compatibility.

            Example:
                \```python
                dbt_check_name("not_null", "orders.id")
                # Returns: "dbt__not_null__orders_id"

                dbt_check_name("accepted_values", "orders.status")
                # Returns: "dbt__accepted_values__orders_status"
                \```

            """
            return f"dbt__{_sanitize_dagster_name(test_type)}__{_sanitize_dagster_name(target)}"
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;test_type&#x22;" type="&#x22;str&#x22;" value="undefined">
          dbt test type (e.g., `not_null`, `unique`, `accepted_values`).
        </PyParameter>

        <PyParameter name="&#x22;target&#x22;" type="&#x22;str&#x22;" value="undefined">
          Target model/column identifier for the test (e.g., `orders.status`).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Canonical check name in `dbt__\<test_type>__\<target>` format,
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_sanitize_dagster_name&#x22;" type="&#x22;(value) -> str&#x22;">
      Normalize a string into a Dagster-safe identifier segment.

      Replaces non-alphanumeric characters with underscores and collapses
      consecutive underscores to produce a clean identifier.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        _sanitize_dagster_name("orders.id")
        # Returns: "orders_id"

        _sanitize_dagster_name("schema.table.column")
        # Returns: "schema_table_column"

        _sanitize_dagster_name("!!!")
        # Returns: "unknown"
        ```
      </Callout>

      <PySourceCode>
        ````python
        def _sanitize_dagster_name(value: str) -> str:
            """Normalize a string into a Dagster-safe identifier segment.

            Replaces non-alphanumeric characters with underscores and collapses
            consecutive underscores to produce a clean identifier.

            Args:
                value: Raw identifier value that may contain special characters.

            Returns:
                Lower-risk identifier containing only alphanumerics and single
                underscores. Returns "unknown" if the result would be empty.

            Example:
                \```python
                _sanitize_dagster_name("orders.id")
                # Returns: "orders_id"

                _sanitize_dagster_name("schema.table.column")
                # Returns: "schema_table_column"

                _sanitize_dagster_name("!!!")
                # Returns: "unknown"
                \```

            """
            cleaned = "".join(char if char.isalnum() else "_" for char in value.strip())
            cleaned = "_".join(part for part in cleaned.split("_") if part)
            return cleaned or "unknown"
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;value&#x22;" type="&#x22;str&#x22;" value="undefined">
          Raw identifier value that may contain special characters.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Lower-risk identifier containing only alphanumerics and single
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
