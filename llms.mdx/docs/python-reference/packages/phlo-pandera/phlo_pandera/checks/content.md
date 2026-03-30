# checks (/docs/python-reference/packages/phlo-pandera/phlo_pandera/checks)



Quality check classes for declarative data validation.

This module provides the core quality check classes for the Phlo Quality Framework.
These classes define validation rules that can be applied to data tables and
integrated into Dagster pipelines via the `@phlo_pandera` decorator.

Each check class implements the `QualityCheck` abstract base class and provides
a declarative way to define validation rules. Checks operate on pandas DataFrames
and return structured `QualityCheckResult` objects containing pass/fail status,
metrics, and metadata.

Quality Check Architecture:
The quality check system follows a consistent pattern:

1. **Definition**: Instantiate check classes with configuration parameters
2. **Execution**: Check classes implement `execute()` method for validation
3. **Results**: Return `QualityCheckResult` with pass/fail and metadata
4. **Integration**: `@phlo_pandera` decorator converts checks to Dagster asset checks

Basic Usage:

```python
from phlo_pandera import NullCheck, RangeCheck, phlo_pandera

@phlo_pandera(
    table="bronze.sensor_readings",
    checks=[
        NullCheck(columns=["sensor_id", "reading_value"]),
        RangeCheck(column="reading_value", min_value=0, max_value=100),
    ],
)
def sensor_quality():
    pass
```

Available Checks:

* **NullCheck**: Validates that specified columns contain no null values
* **RangeCheck**: Validates that numeric column values fall within a specified range
* **FreshnessCheck**: Validates that data is recent based on timestamp columns
* **UniqueCheck**: Validates uniqueness constraints across specified columns
* **CountCheck**: Validates that row count meets minimum and/or maximum bounds

Thresholds and Tolerance:
Most checks support threshold parameters that allow a configurable percentage
of failures before marking the check as failed:

```python
# Allow up to 5% null values before failing
NullCheck(columns=["optional_field"], allow_threshold=0.05)

# Allow up to 1% out-of-range values
RangeCheck(column="measurement", min_value=0, max_value=100, allow_threshold=0.01)
```

Type Aliases:

* `MetricValue`: Union of int, float, dict, or None for metric values
* `Metadata`: Dictionary for arbitrary metadata

See Also:

* `checks_extra.py`: Extended check types (SchemaCheck, CustomSQLCheck, PatternCheck)
* `reconciliation.py`: Cross-table reconciliation checks
* `decorator.py`: `@phlo_pandera` decorator implementation

<PyAttribute name="&#x22;MetricValue&#x22;" type="null" value="&#x22;int | float | dict[str, Any] | None&#x22;" />

<PyAttribute name="&#x22;Metadata&#x22;" type="null" value="&#x22;dict[str, Any]&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;QualityCheckResult&#x22;" href="&#x22;/docs/python-reference/packages/phlo-pandera/phlo_pandera/checks/QualityCheckResult&#x22;" />

      <Card title="&#x22;QualityCheck&#x22;" href="&#x22;/docs/python-reference/packages/phlo-pandera/phlo_pandera/checks/QualityCheck&#x22;" />

      <Card title="&#x22;NullCheck&#x22;" href="&#x22;/docs/python-reference/packages/phlo-pandera/phlo_pandera/checks/NullCheck&#x22;" />

      <Card title="&#x22;RangeCheck&#x22;" href="&#x22;/docs/python-reference/packages/phlo-pandera/phlo_pandera/checks/RangeCheck&#x22;" />

      <Card title="&#x22;FreshnessCheck&#x22;" href="&#x22;/docs/python-reference/packages/phlo-pandera/phlo_pandera/checks/FreshnessCheck&#x22;" />

      <Card title="&#x22;UniqueCheck&#x22;" href="&#x22;/docs/python-reference/packages/phlo-pandera/phlo_pandera/checks/UniqueCheck&#x22;" />

      <Card title="&#x22;CountCheck&#x22;" href="&#x22;/docs/python-reference/packages/phlo-pandera/phlo_pandera/checks/CountCheck&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;extract_sample_rows&#x22;" type="&#x22;(df, mask, columns, max_rows=20) -> list[dict[str, Any]]&#x22;">
      Extract sample rows matching a condition for error reporting.

      This helper function extracts a sample of rows that match a boolean mask,
      limited to a maximum number of rows. It's used to provide concrete examples
      of quality check failures for debugging and reporting purposes.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        import pandas as pd

        df = pd.DataFrame(\{
            "id": [1, 2, 3, 4],
            "value": [100, None, 300, None]
        \})

        null_mask = df["value"].isna()
        samples = extract_sample_rows(df, null_mask, ["id", "value"], max_rows=10)
        # Returns: [\{"row_index": 1, "id": 2, "value": None\}, ...]
        ```
      </Callout>

      <PySourceCode>
        ````python
        def extract_sample_rows(
            df: pd.DataFrame,
            mask: pd.Series,
            columns: list[str],
            max_rows: int = 20,
        ) -> list[dict[str, Any]]:
            """Extract sample rows matching a condition for error reporting.

            This helper function extracts a sample of rows that match a boolean mask,
            limited to a maximum number of rows. It's used to provide concrete examples
            of quality check failures for debugging and reporting purposes.

            Args:
                df: DataFrame to sample from.
                mask: Boolean Series indicating which rows to extract.
                columns: List of column names to include in the sample.
                max_rows: Maximum number of rows to return (default: 20).

            Returns:
                List of dictionaries, each representing a sampled row with its index
                and specified column values.

            Example:
                \```python
                import pandas as pd

                df = pd.DataFrame({
                    "id": [1, 2, 3, 4],
                    "value": [100, None, 300, None]
                })

                null_mask = df["value"].isna()
                samples = extract_sample_rows(df, null_mask, ["id", "value"], max_rows=10)
                # Returns: [{"row_index": 1, "id": 2, "value": None}, ...]
                \```

            """
            rows = df.loc[mask, columns].head(max_rows)
            return [
                {"row_index": idx if isinstance(idx, int) else str(idx), **row.to_dict()}
                for idx, row in rows.iterrows()
            ]
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;df&#x22;" type="&#x22;pd.DataFrame&#x22;" value="undefined">
          DataFrame to sample from.
        </PyParameter>

        <PyParameter name="&#x22;mask&#x22;" type="&#x22;pd.Series&#x22;" value="undefined">
          Boolean Series indicating which rows to extract.
        </PyParameter>

        <PyParameter name="&#x22;columns&#x22;" type="&#x22;list[str]&#x22;" value="undefined">
          List of column names to include in the sample.
        </PyParameter>

        <PyParameter name="&#x22;max_rows&#x22;" type="&#x22;int&#x22;" value="&#x22;20&#x22;">
          Maximum number of rows to return (default: 20).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        List of dictionaries, each representing a sampled row with its index
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
