# QualityCheckContract (/docs/python-reference/packages/phlo-pandera/phlo_pandera/contract/QualityCheckContract)



Canonical metadata payload for quality checks.

This dataclass provides a standardized structure for quality check results
that can be serialized to metadata and consumed by downstream systems like
the Observatory UI or alerting systems.

Using `frozen=True` and `slots=True` provides immutability and memory
efficiency for these frequently created objects.

Attributes [#attributes]

<PyAttribute name="&#x22;source&#x22;" type="&#x22;Literal['pandera', 'dbt', 'phlo']&#x22;" value="null">
  Check source type (`pandera`, `dbt`, or `phlo`).
</PyAttribute>

<PyAttribute name="&#x22;failed_count&#x22;" type="&#x22;int&#x22;" value="null">
  Number of observed failures during check execution.
</PyAttribute>

<PyAttribute name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Optional partition key for scoped checks (YYYY-MM-DD format).
</PyAttribute>

<PyAttribute name="&#x22;total_count&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;">
  Optional total evaluated count (rows, tests, etc.).
</PyAttribute>

<PyAttribute name="&#x22;query_or_sql&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Optional query or SQL used for evaluation.
</PyAttribute>

<PyAttribute name="&#x22;repro_sql&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
  Optional reproduction SQL snippet for debugging.
</PyAttribute>

<PyAttribute name="&#x22;sample&#x22;" type="&#x22;list[Any] | None&#x22;" value="&#x22;None&#x22;">
  Optional failure samples, trimmed to 20 items on export.
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;to_metadata&#x22;" type="&#x22;(self) -> dict[str, Any]&#x22;">
  Export contract fields as a metadata dictionary.

  Converts the contract dataclass into a dictionary with standardized
  keys for consumption by Dagster metadata and downstream systems.
  Automatically limits samples to 20 items.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    ```python
    contract = QualityCheckContract(
        source="pandera",
        failed_count=5,
        partition_key="2024-01-15",
    )
    metadata = contract.to_metadata()
    # Returns: \{"source": "pandera", "failed_count": 5, "partition_key": "2024-01-15"\}
    ```
  </Callout>

  <PySourceCode>
    ````python
    def to_metadata(self) -> dict[str, Any]:
        """Export contract fields as a metadata dictionary.

        Converts the contract dataclass into a dictionary with standardized
        keys for consumption by Dagster metadata and downstream systems.
        Automatically limits samples to 20 items.

        Returns:
            Dictionary containing all non-None contract fields using the
            quality-check contract key naming convention.

        Example:
            \```python
            contract = QualityCheckContract(
                source="pandera",
                failed_count=5,
                partition_key="2024-01-15",
            )
            metadata = contract.to_metadata()
            # Returns: {"source": "pandera", "failed_count": 5, "partition_key": "2024-01-15"}
            \```

        """
        metadata: dict[str, Any] = {
            "source": self.source,
            "failed_count": self.failed_count,
        }

        if self.partition_key is not None:
            metadata["partition_key"] = self.partition_key

        if self.total_count is not None:
            metadata["total_count"] = self.total_count

        if self.query_or_sql is not None:
            metadata["query_or_sql"] = self.query_or_sql

        if self.repro_sql is not None:
            metadata["repro_sql"] = self.repro_sql

        if self.sample is not None:
            metadata["sample"] = self.sample[:20]

        return metadata
    ````
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary containing all non-None contract fields using the
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;to_dagster_metadata&#x22;" type="&#x22;(self) -> dict[str, Any]&#x22;">
  Backwards-compatible alias for metadata consumers.

  This method provides compatibility with older code that expects
  the `to_dagster_metadata` method name. It simply delegates to
  `to_metadata()`.

  <PySourceCode>
    ```python
    def to_dagster_metadata(self) -> dict[str, Any]:
        """Backwards-compatible alias for metadata consumers.

        This method provides compatibility with older code that expects
        the ``to_dagster_metadata`` method name. It simply delegates to
        ``to_metadata()``.

        Returns:
            Dictionary from ``to_metadata()``.

        """
        return self.to_metadata()
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;dict&#x22;">
    Dictionary from `to_metadata()`.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, source, failed_count, partition_key=None, total_count=None, query_or_sql=None, repro_sql=None, sample=None) -> None&#x22;">
  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;source&#x22;" type="&#x22;Literal['pandera', 'dbt', 'phlo']&#x22;" value="null" />

    <PyParameter name="&#x22;failed_count&#x22;" type="&#x22;int&#x22;" value="null" />

    <PyParameter name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;total_count&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;query_or_sql&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;repro_sql&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

    <PyParameter name="&#x22;sample&#x22;" type="&#x22;list[Any] | None&#x22;" value="&#x22;None&#x22;" />
  </div>

  <PyFunctionReturn type="&#x22;None&#x22;" />
</PyFunction>
