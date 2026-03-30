# decorator_helpers (/docs/python-reference/packages/phlo-pandera/phlo_pandera/decorator_helpers)



Private helper functions for the @phlo\_pandera decorator.

This module contains internal implementation details for the `@phlo_pandera`
decorator. These functions are not part of the public API and may change
without notice. Users should interact with the decorator through the public
interface in `decorator.py`.

The helpers in this module handle:

* Event emitter creation for quality results and telemetry
* Data loading from Trino or DuckDB backends
* Metadata building for check results
* Failure estimation and sampling
* Contract metadata generation
* SQL reproduction helpers

Example:
These functions are used internally by the decorator:

```python
from phlo_pandera.decorator_helpers import _make_emitters, _load_data

# Create emitters for event publishing
emitter, telemetry = _make_emitters(
    runtime=context,
    asset_key="customers",
    partition_key_value="2024-01-15",
    source="phlo",
    backend="trino",
)

# Load data from configured backend
df = _load_data(runtime=context, query="SELECT * FROM bronze.customers", backend="trino")
```

Note:
All functions in this module are prefixed with underscore to indicate
they are private implementation details.

See Also:

* `decorator.py`: Public `@phlo_pandera` decorator
* `checks.py`: Quality check implementations that use these helpers

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_make_emitters&#x22;" type="&#x22;(runtime, asset_key, partition_key_value, source, backend) -> tuple[QualityResultEventEmitter, TelemetryEventEmitter]&#x22;">
      Create quality-result and telemetry emitters for event publishing.

      Sets up event emitters with proper correlation context for tracking
      quality check results and telemetry metrics through the Phlo hooks system.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        emitter, telemetry = _make_emitters(
            runtime=context,
            asset_key="orders",
            partition_key_value="2024-01-15",
            source="phlo",
            backend="trino",
        )

        # Emit a quality result
        emitter.emit_result(
            check_name="null_check",
            passed=True,
            check_type="null",
            metadata=\{"null_count": 0\},
        )
        ```
      </Callout>

      <PySourceCode>
        ````python
        def _make_emitters(
            runtime: RuntimeContext,
            asset_key: str,
            partition_key_value: str | None,
            source: str,
            backend: str,
        ) -> tuple[QualityResultEventEmitter, TelemetryEventEmitter]:
            """Create quality-result and telemetry emitters for event publishing.

            Sets up event emitters with proper correlation context for tracking
            quality check results and telemetry metrics through the Phlo hooks system.

            Args:
                runtime: Runtime context containing run_id and resources.
                asset_key: Asset identifier being checked.
                partition_key_value: Partition key for partitioned assets, or None.
                source: Source identifier (e.g., "phlo", "pandera").
                backend: Backend identifier (e.g., "trino", "duckdb").

            Returns:
                Tuple of (quality_result_emitter, telemetry_emitter) configured with
                the appropriate correlation context.

            Example:
                \```python
                emitter, telemetry = _make_emitters(
                    runtime=context,
                    asset_key="orders",
                    partition_key_value="2024-01-15",
                    source="phlo",
                    backend="trino",
                )

                # Emit a quality result
                emitter.emit_result(
                    check_name="null_check",
                    passed=True,
                    check_type="null",
                    metadata={"null_count": 0},
                )
                \```

            """
            correlation = HookCorrelation(
                run_id=runtime.run_id,
                asset_key=asset_key,
                partition_key=partition_key_value,
                job_name=getattr(runtime, "job_name", None),
            )
            emitter = QualityResultEventEmitter(
                QualityResultEventContext(
                    asset_key=asset_key,
                    run_id=runtime.run_id,
                    partition_key=partition_key_value,
                    tags={"source": source, "backend": backend},
                    correlation=correlation,
                )
            )
            telemetry = TelemetryEventEmitter(
                TelemetryEventContext(
                    tags={
                        "asset": asset_key,
                        "source": source,
                        "backend": backend,
                    },
                    correlation=correlation,
                )
            )
            return emitter, telemetry
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;runtime&#x22;" type="&#x22;RuntimeContext&#x22;" value="undefined">
          Runtime context containing run\_id and resources.
        </PyParameter>

        <PyParameter name="&#x22;asset_key&#x22;" type="&#x22;str&#x22;" value="undefined">
          Asset identifier being checked.
        </PyParameter>

        <PyParameter name="&#x22;partition_key_value&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Partition key for partitioned assets, or None.
        </PyParameter>

        <PyParameter name="&#x22;source&#x22;" type="&#x22;str&#x22;" value="undefined">
          Source identifier (e.g., "phlo", "pandera").
        </PyParameter>

        <PyParameter name="&#x22;backend&#x22;" type="&#x22;str&#x22;" value="undefined">
          Backend identifier (e.g., "trino", "duckdb").
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo.hooks.QualityResultEventEmitter&#x22;">
        Tuple of (quality\_result\_emitter, telemetry\_emitter) configured with
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_load_data&#x22;" type="&#x22;(runtime, query, backend) -> Any&#x22;">
      Resolve the backend resource and load data as a DataFrame.

      Dispatches to the appropriate backend-specific loader based on the
      configured backend type. Supports "trino" and "duckdb" backends.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        df = _load_data(
            runtime=context,
            query="SELECT * FROM bronze.events",
            backend="trino",
        )
        ```
      </Callout>

      <PySourceCode>
        ````python
        def _load_data(
            runtime: RuntimeContext,
            query: str,
            backend: str,
        ) -> Any:
            """Resolve the backend resource and load data as a DataFrame.

            Dispatches to the appropriate backend-specific loader based on the
            configured backend type. Supports "trino" and "duckdb" backends.

            Args:
                runtime: Runtime context with resources and logging.
                query: SQL query to execute for data loading.
                backend: Backend type ("trino" or "duckdb").

            Returns:
                DataFrame containing query results (pandas DataFrame).

            Raises:
                ValueError: If an unknown backend is specified.

            Example:
                \```python
                df = _load_data(
                    runtime=context,
                    query="SELECT * FROM bronze.events",
                    backend="trino",
                )
                \```

            """
            if backend == "trino":
                trino = _resolve_trino_resource(runtime)
                return _load_data_trino(runtime, query, trino)
            elif backend == "duckdb":
                duckdb_conn = _resolve_duckdb_connection(runtime)
                return _load_data_duckdb(runtime, query, duckdb_conn)
            else:
                raise ValueError(f"Unknown backend: {backend}")
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;runtime&#x22;" type="&#x22;RuntimeContext&#x22;" value="undefined">
          Runtime context with resources and logging.
        </PyParameter>

        <PyParameter name="&#x22;query&#x22;" type="&#x22;str&#x22;" value="undefined">
          SQL query to execute for data loading.
        </PyParameter>

        <PyParameter name="&#x22;backend&#x22;" type="&#x22;str&#x22;" value="undefined">
          Backend type ("trino" or "duckdb").
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;typing.Any&#x22;">
        DataFrame containing query results (pandas DataFrame).
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_load_data_trino&#x22;" type="&#x22;(context, query, trino) -> Any&#x22;">
      Load data from Trino into a pandas DataFrame.

      Executes the query using a Trino cursor, fetches all results, and
      constructs a pandas DataFrame with proper column names from cursor
      description metadata.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        trino = _resolve_trino_resource(context)
        df = _load_data_trino(context, "SELECT * FROM events", trino)
        ```
      </Callout>

      <PySourceCode>
        ````python
        def _load_data_trino(context: RuntimeContext, query: str, trino: Any) -> Any:
            """Load data from Trino into a pandas DataFrame.

            Executes the query using a Trino cursor, fetches all results, and
            constructs a pandas DataFrame with proper column names from cursor
            description metadata.

            Args:
                context: Runtime context for logging.
                query: SQL query to execute.
                trino: Trino resource/connection object.

            Returns:
                pandas DataFrame with query results.

            Raises:
                ValueError: If Trino returns no column metadata.

            Example:
                \```python
                trino = _resolve_trino_resource(context)
                df = _load_data_trino(context, "SELECT * FROM events", trino)
                \```

            """
            import pandas as pd

            # Execute query
            with trino.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()

                if not cursor.description:
                    raise ValueError("Trino did not return column metadata")

                columns = [desc[0] for desc in cursor.description]

            # Convert to DataFrame
            df = pd.DataFrame(rows, columns=columns)

            context.logger.info("loaded_rows_from_trino", row_count=len(df))

            return df
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;context&#x22;" type="&#x22;RuntimeContext&#x22;" value="undefined">
          Runtime context for logging.
        </PyParameter>

        <PyParameter name="&#x22;query&#x22;" type="&#x22;str&#x22;" value="undefined">
          SQL query to execute.
        </PyParameter>

        <PyParameter name="&#x22;trino&#x22;" type="&#x22;Any&#x22;" value="undefined">
          Trino resource/connection object.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;typing.Any&#x22;">
        pandas DataFrame with query results.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_resolve_trino_resource&#x22;" type="&#x22;(context) -> Any&#x22;">
      Resolve Trino resource from context or create a default connection.

      Attempts to find a Trino resource in multiple locations:

      1. context.resources dictionary
      2. context.resources attributes
      3. context.get\_resource("trino")
      4. Creates a new TrinoResource if phlo\_trino is available

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        trino = _resolve_trino_resource(context)
        ```
      </Callout>

      <PySourceCode>
        ````python
        def _resolve_trino_resource(context: RuntimeContext) -> Any:
            """Resolve Trino resource from context or create a default connection.

            Attempts to find a Trino resource in multiple locations:
            1. context.resources dictionary
            2. context.resources attributes
            3. context.get_resource("trino")
            4. Creates a new TrinoResource if phlo_trino is available

            Args:
                context: Runtime context that may contain Trino resource.

            Returns:
                Trino resource object ready for query execution.

            Raises:
                ValueError: If no Trino resource can be found or created.

            Example:
                \```python
                trino = _resolve_trino_resource(context)
                \```

            """
            trino = None
            resources = context.resources
            if isinstance(resources, dict):
                trino = resources.get("trino")
            elif resources is not None:
                trino = getattr(resources, "trino", None)
            if trino is None:
                try:
                    trino = context.get_resource("trino")
                except Exception:
                    trino = None
            if trino is None:
                try:
                    from phlo_trino.resource import TrinoResource
                except Exception as exc:  # noqa: BLE001 - surface missing backend cleanly
                    raise ValueError(
                        "Trino resource not found in context and phlo_trino is not available"
                    ) from exc
                trino = TrinoResource()
            return trino
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;context&#x22;" type="&#x22;RuntimeContext&#x22;" value="undefined">
          Runtime context that may contain Trino resource.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;typing.Any&#x22;">
        Trino resource object ready for query execution.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_resolve_duckdb_connection&#x22;" type="&#x22;(context) -> Any&#x22;">
      Resolve DuckDB connection from context or create a default connection.

      Attempts to find a DuckDB resource in multiple locations:

      1. context.resources dictionary
      2. context.resources attributes
      3. context.get\_resource("duckdb")
      4. Creates a new in-memory DuckDB connection

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        duckdb_conn = _resolve_duckdb_connection(context)
        ```
      </Callout>

      <PySourceCode>
        ````python
        def _resolve_duckdb_connection(context: RuntimeContext) -> Any:
            """Resolve DuckDB connection from context or create a default connection.

            Attempts to find a DuckDB resource in multiple locations:
            1. context.resources dictionary
            2. context.resources attributes
            3. context.get_resource("duckdb")
            4. Creates a new in-memory DuckDB connection

            Args:
                context: Runtime context that may contain DuckDB resource.

            Returns:
                DuckDB connection object ready for query execution.

            Raises:
                ValueError: If no DuckDB connection can be found or created.

            Example:
                \```python
                duckdb_conn = _resolve_duckdb_connection(context)
                \```

            """
            duckdb_conn = None
            resources = context.resources
            if isinstance(resources, dict):
                duckdb_conn = resources.get("duckdb")
            elif resources is not None:
                duckdb_conn = getattr(resources, "duckdb", None)
            if duckdb_conn is None:
                try:
                    duckdb_conn = context.get_resource("duckdb")
                except Exception:
                    duckdb_conn = None
            if duckdb_conn is None:
                try:
                    import duckdb
                except Exception as exc:  # noqa: BLE001 - surface missing backend cleanly
                    raise ValueError(
                        "DuckDB resource not found in context and duckdb is not available"
                    ) from exc
                duckdb_conn = duckdb.connect()
            return duckdb_conn
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;context&#x22;" type="&#x22;RuntimeContext&#x22;" value="undefined">
          Runtime context that may contain DuckDB resource.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;typing.Any&#x22;">
        DuckDB connection object ready for query execution.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_load_data_duckdb&#x22;" type="&#x22;(context, query, duckdb_conn) -> Any&#x22;">
      Load data from DuckDB into a pandas DataFrame.

      Executes the query using DuckDB and returns results as a DataFrame.
      DuckDB's fetchdf() method handles the conversion automatically.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        duckdb_conn = _resolve_duckdb_connection(context)
        df = _load_data_duckdb(context, "SELECT * FROM local_table", duckdb_conn)
        ```
      </Callout>

      <PySourceCode>
        ````python
        def _load_data_duckdb(context: RuntimeContext, query: str, duckdb_conn: Any) -> Any:
            """Load data from DuckDB into a pandas DataFrame.

            Executes the query using DuckDB and returns results as a DataFrame.
            DuckDB's fetchdf() method handles the conversion automatically.

            Args:
                context: Runtime context for logging.
                query: SQL query to execute.
                duckdb_conn: DuckDB connection object.

            Returns:
                pandas DataFrame with query results.

            Example:
                \```python
                duckdb_conn = _resolve_duckdb_connection(context)
                df = _load_data_duckdb(context, "SELECT * FROM local_table", duckdb_conn)
                \```

            """

            # Execute query
            df = duckdb_conn.execute(query).fetchdf()

            context.logger.info("loaded_rows_from_duckdb", row_count=len(df))

            return df
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;context&#x22;" type="&#x22;RuntimeContext&#x22;" value="undefined">
          Runtime context for logging.
        </PyParameter>

        <PyParameter name="&#x22;query&#x22;" type="&#x22;str&#x22;" value="undefined">
          SQL query to execute.
        </PyParameter>

        <PyParameter name="&#x22;duckdb_conn&#x22;" type="&#x22;Any&#x22;" value="undefined">
          DuckDB connection object.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;typing.Any&#x22;">
        pandas DataFrame with query results.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_build_metadata&#x22;" type="&#x22;(df, check_results) -> dict[str, Any]&#x22;">
      Build metadata dictionary for downstream consumers.

      Aggregates check results into a comprehensive metadata dictionary suitable
      for Dagster metadata and observability systems. Includes summary tables and
      individual check metrics.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        results = [null_result, range_result]
        metadata = _build_metadata(df, results)
        # metadata contains:
        # - rows_validated, columns_validated
        # - checks_executed, checks_passed, checks_failed
        # - Individual results keyed by metric_name
        # - quality_summary: Markdown table
        ```
      </Callout>

      <PySourceCode>
        ````python
        def _build_metadata(df: Any, check_results: List[QualityCheckResult]) -> dict[str, Any]:
            """Build metadata dictionary for downstream consumers.

            Aggregates check results into a comprehensive metadata dictionary suitable
            for Dagster metadata and observability systems. Includes summary tables and
            individual check metrics.

            Args:
                df: DataFrame that was validated (for row/column counts).
                check_results: List of QualityCheckResult objects from executed checks.

            Returns:
                Dictionary with aggregated metadata including:
                - Row and column counts
                - Pass/fail counts
                - Individual metric values
                - Formatted summary table (Markdown)

            Example:
                \```python
                results = [null_result, range_result]
                metadata = _build_metadata(df, results)
                # metadata contains:
                # - rows_validated, columns_validated
                # - checks_executed, checks_passed, checks_failed
                # - Individual results keyed by metric_name
                # - quality_summary: Markdown table
                \```

            """
            metadata: dict[str, Any] = {
                "rows_validated": len(df),
                "columns_validated": len(df.columns),
                "checks_executed": len(check_results),
                "checks_passed": sum(1 for r in check_results if r.passed),
                "checks_failed": sum(1 for r in check_results if not r.passed),
            }

            # Add individual check results
            for result in check_results:
                # Add metric value
                if result.metric_value is not None:
                    metadata[f"{result.metric_name}_value"] = result.metric_value

                # Add check metadata
                if result.metadata:
                    for key, value in result.metadata.items():
                        metadata_key = f"{result.metric_name}_{key}"
                        metadata[metadata_key] = value

            # Build quality summary table
            summary_rows = []
            for result in check_results:
                summary_rows.append(
                    f"| {result.metric_name} | {'✅ Pass' if result.passed else '❌ Fail'} | "
                    f"{result.metric_value} | {result.failure_message or '-'} |"
                )

            if summary_rows:
                summary_table = (
                    "## Quality Check Results\n\n"
                    "| Check | Status | Value | Message |\n"
                    "|-------|--------|-------|----------|\n" + "\n".join(summary_rows)
                )
                metadata["quality_summary"] = summary_table

            return metadata
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;df&#x22;" type="&#x22;Any&#x22;" value="undefined">
          DataFrame that was validated (for row/column counts).
        </PyParameter>

        <PyParameter name="&#x22;check_results&#x22;" type="&#x22;List[QualityCheckResult]&#x22;" value="undefined">
          List of QualityCheckResult objects from executed checks.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Dictionary with aggregated metadata including:
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_estimate_failed_count&#x22;" type="&#x22;(check_results) -> int&#x22;">
      Estimate total failed row count from check results.

      Attempts to extract failure counts from result metadata using various
      known keys. Falls back to counting failed checks if no row counts found.

      Known metadata keys checked:

      * "failed\_rows"
      * "failure\_count"
      * "duplicate\_count"
      * "out\_of\_range"
      * "non\_match\_count"

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        failed_count = _estimate_failed_count(check_results)
        # Returns: sum of detected failures across all checks
        ```
      </Callout>

      <PySourceCode>
        ````python
        def _estimate_failed_count(check_results: List[QualityCheckResult]) -> int:
            """Estimate total failed row count from check results.

            Attempts to extract failure counts from result metadata using various
            known keys. Falls back to counting failed checks if no row counts found.

            Known metadata keys checked:
            - "failed_rows"
            - "failure_count"
            - "duplicate_count"
            - "out_of_range"
            - "non_match_count"

            Args:
                check_results: List of QualityCheckResult objects.

            Returns:
                Estimated count of failed rows across all checks, or count of
                failed checks if no row counts available.

            Example:
                \```python
                failed_count = _estimate_failed_count(check_results)
                # Returns: sum of detected failures across all checks
                \```

            """
            failed_count = 0
            for result in check_results:
                if result.passed:
                    continue
                metadata = result.metadata or {}
                for key in (
                    "failed_rows",
                    "failure_count",
                    "duplicate_count",
                    "out_of_range",
                    "non_match_count",
                ):
                    value = metadata.get(key)
                    if isinstance(value, int):
                        failed_count += value
                        break
            if failed_count > 0:
                return failed_count
            return sum(1 for r in check_results if not r.passed)
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;check_results&#x22;" type="&#x22;List[QualityCheckResult]&#x22;" value="undefined">
          List of QualityCheckResult objects.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;int&#x22;">
        Estimated count of failed rows across all checks, or count of
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_collect_failure_sample&#x22;" type="&#x22;(check_results) -> list[dict[str, Any]]&#x22;">
      Collect sample failure rows from check results.

      Aggregates sample rows from failed checks into a unified sample list,
      limited to 20 rows total for metadata efficiency.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        sample = _collect_failure_sample(check_results)
        # Returns: [\{"check": "null_check", "row_index": 5, "column": "email"\}, ...]
        ```
      </Callout>

      <PySourceCode>
        ````python
        def _collect_failure_sample(check_results: List[QualityCheckResult]) -> list[dict[str, Any]]:
            """Collect sample failure rows from check results.

            Aggregates sample rows from failed checks into a unified sample list,
            limited to 20 rows total for metadata efficiency.

            Args:
                check_results: List of QualityCheckResult objects.

            Returns:
                List of sample failure dictionaries, each tagged with the check name
                that produced it. Maximum 20 items.

            Example:
                \```python
                sample = _collect_failure_sample(check_results)
                # Returns: [{"check": "null_check", "row_index": 5, "column": "email"}, ...]
                \```

            """
            sample: list[dict[str, Any]] = []
            for result in check_results:
                if result.passed:
                    continue
                rows = result.metadata.get("sample_rows") if result.metadata else None
                if not isinstance(rows, list):
                    continue
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    sample.append({"check": result.metric_name, **row})
                    if len(sample) >= 20:
                        return sample
            return sample
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;check_results&#x22;" type="&#x22;List[QualityCheckResult]&#x22;" value="undefined">
          List of QualityCheckResult objects.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        List of sample failure dictionaries, each tagged with the check name
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_contract_metadata&#x22;" type="&#x22;(contract) -> dict[str, Any]&#x22;">
      Convert QualityCheckContract to metadata dictionary.

      Extracts non-None fields from the contract into a flat metadata dictionary
      suitable for Dagster metadata.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        contract = QualityCheckContract(
            source="phlo",
            failed_count=5,
            partition_key="2024-01-15",
        )
        metadata = _contract_metadata(contract)
        # Returns: \{"source": "phlo", "failed_count": 5, "partition_key": "2024-01-15"\}
        ```
      </Callout>

      <PySourceCode>
        ````python
        def _contract_metadata(contract: QualityCheckContract) -> dict[str, Any]:
            """Convert QualityCheckContract to metadata dictionary.

            Extracts non-None fields from the contract into a flat metadata dictionary
            suitable for Dagster metadata.

            Args:
                contract: QualityCheckContract instance.

            Returns:
                Dictionary with contract fields as metadata keys.

            Example:
                \```python
                contract = QualityCheckContract(
                    source="phlo",
                    failed_count=5,
                    partition_key="2024-01-15",
                )
                metadata = _contract_metadata(contract)
                # Returns: {"source": "phlo", "failed_count": 5, "partition_key": "2024-01-15"}
                \```

            """
            metadata: dict[str, Any] = {"source": contract.source, "failed_count": contract.failed_count}
            if contract.partition_key is not None:
                metadata["partition_key"] = contract.partition_key
            if contract.total_count is not None:
                metadata["total_count"] = contract.total_count
            if contract.query_or_sql is not None:
                metadata["query_or_sql"] = contract.query_or_sql
            if contract.repro_sql is not None:
                metadata["repro_sql"] = contract.repro_sql
            if contract.sample is not None:
                metadata["sample"] = contract.sample[:20]
            return metadata
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;contract&#x22;" type="&#x22;QualityCheckContract&#x22;" value="undefined">
          QualityCheckContract instance.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Dictionary with contract fields as metadata keys.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_repro_sql&#x22;" type="&#x22;(query) -> str&#x22;">
      Generate reproducible SQL snippet with safety limits.

      Wraps a query in a subquery and adds a LIMIT clause to make it safe
      for ad-hoc execution and debugging.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        repro = _repro_sql("SELECT * FROM large_table")
        # Returns:
        # SELECT *
        # FROM (
        # SELECT * FROM large_table
        # ) AS phlo_pandera
        # LIMIT 100
        ```
      </Callout>

      <PySourceCode>
        ````python
        def _repro_sql(query: str) -> str:
            """Generate reproducible SQL snippet with safety limits.

            Wraps a query in a subquery and adds a LIMIT clause to make it safe
            for ad-hoc execution and debugging.

            Args:
                query: Original SQL query.

            Returns:
                SQL string wrapped with LIMIT 100 for safe reproduction.

            Example:
                \```python
                repro = _repro_sql("SELECT * FROM large_table")
                # Returns:
                # SELECT *
                # FROM (
                # SELECT * FROM large_table
                # ) AS phlo_pandera
                # LIMIT 100
                \```

            """
            return f"SELECT *\nFROM (\n{query}\n) AS phlo_pandera\nLIMIT 100"
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;query&#x22;" type="&#x22;str&#x22;" value="undefined">
          Original SQL query.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        SQL string wrapped with LIMIT 100 for safe reproduction.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
