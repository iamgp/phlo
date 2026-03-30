# pandera_checks (/docs/python-reference/packages/phlo-dlt/phlo_dlt/pandera_checks)



Pandera contract checks for DLT ingestion assets.

This module provides Pandera schema validation integration for DLT-based
ingestion pipelines. It handles the evaluation of data contracts against
staged Parquet files and converts validation results into Phlo-compatible
check results.

Key Components:

* :class:`PanderaContractEvaluation`: Result container for validation outcomes
* :class:`PanderaContractValidationError`: Exception for validation failures
* :func:`evaluate_pandera_contract`: Validate DataFrame against schema
* :func:`evaluate_pandera_contract_parquet`: Validate single Parquet file
* :func:`evaluate_pandera_contract_parquet_files`: Validate multiple Parquet files
* :func:`pandera_contract_asset_check_result`: Convert to Phlo check result
* :func:`serialize_pandera_contract_evaluation`: Serialize evaluation to dict
* :func:`deserialize_pandera_contract_evaluation`: Deserialize from dict

Validation Flow:

1. DLT extracts data to Parquet files
2. Parquet files are validated against Pandera schema
3. Results are converted to Phlo check results
4. In strict mode, failures abort before data is visible

See Also:

* :mod:`phlo_dlt.decorator`: Decorator that orchestrates validation
* :mod:`phlo_dlt.executor`: Executor that triggers validation
* Pandera documentation: [https://pandera.readthedocs.io/](https://pandera.readthedocs.io/)

<PyAttribute name="&#x22;PANDERA_CONTRACT_CHECK_NAME&#x22;" type="null" value="&#x22;'pandera_contract'&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;PanderaContractEvaluation&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dlt/phlo_dlt/pandera_checks/PanderaContractEvaluation&#x22;" />

      <Card title="&#x22;PanderaContractValidationError&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dlt/phlo_dlt/pandera_checks/PanderaContractValidationError&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;evaluate_pandera_contract_parquet&#x22;" type="&#x22;(parquet_path, *, schema_class) -> PanderaContractEvaluation&#x22;">
      Load parquet data and validate it against a Pandera schema class.

      Reads a Parquet file into a pandas DataFrame and validates it against
      the provided Pandera schema class.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        from pathlib import Path
        from phlo_dlt.pandera_checks import evaluate_pandera_contract_parquet

        result = evaluate_pandera_contract_parquet(
            Path("/tmp/data.parquet"),
            schema_class=UserSchema,
        )
        print(f"Passed: \{result.passed\}, Failed: \{result.failed_count\}")
        ```
      </Callout>

      <Callout title="&#x22;See Also&#x22;" type="&#x22;see-also&#x22;">
        :func:`evaluate_pandera_contract`: Core validation logic.
        :func:`evaluate_pandera_contract_parquet_files`: For multiple files.
      </Callout>

      <PySourceCode>
        ````python
        def evaluate_pandera_contract_parquet(
            parquet_path: Path,
            *,
            schema_class: type[DataFrameModel],
        ) -> PanderaContractEvaluation:
            """Load parquet data and validate it against a Pandera schema class.

            Reads a Parquet file into a pandas DataFrame and validates it against
            the provided Pandera schema class.

            Args:
                parquet_path: Path to the Parquet file to validate.
                schema_class: Pandera DataFrameModel subclass defining validation rules.

            Returns:
                PanderaContractEvaluation: Result of the validation.

            Example:
                \```python
                from pathlib import Path
                from phlo_dlt.pandera_checks import evaluate_pandera_contract_parquet

                result = evaluate_pandera_contract_parquet(
                    Path("/tmp/data.parquet"),
                    schema_class=UserSchema,
                )
                print(f"Passed: {result.passed}, Failed: {result.failed_count}")
                \```

            See Also:
                :func:`evaluate_pandera_contract`: Core validation logic.
                :func:`evaluate_pandera_contract_parquet_files`: For multiple files.

            """
            df = pd.read_parquet(parquet_path)
            return evaluate_pandera_contract(df, schema_class=schema_class)
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;parquet_path&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Path to the Parquet file to validate.
        </PyParameter>

        <PyParameter name="&#x22;schema_class&#x22;" type="&#x22;type[DataFrameModel]&#x22;" value="undefined">
          Pandera DataFrameModel subclass defining validation rules.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_dlt.pandera_checks.PanderaContractEvaluation&#x22;">
        Result of the validation.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;evaluate_pandera_contract_parquet_files&#x22;" type="&#x22;(parquet_paths, *, schema_class) -> PanderaContractEvaluation&#x22;">
      Load one or more parquet files and validate them as a single staged dataset.

      Reads multiple Parquet files, concatenates them into a single DataFrame,
      and validates against the provided schema. This is useful when DLT
      produces multiple Parquet files for a single ingestion run.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        from pathlib import Path
        from phlo_dlt.pandera_checks import evaluate_pandera_contract_parquet_files

        paths = [Path("/tmp/part1.parquet"), Path("/tmp/part2.parquet")]
        result = evaluate_pandera_contract_parquet_files(
            paths,
            schema_class=UserSchema,
        )
        ```
      </Callout>

      <Callout title="&#x22;See Also&#x22;" type="&#x22;see-also&#x22;">
        :func:`evaluate_pandera_contract_parquet`: For single file validation.
      </Callout>

      <PySourceCode>
        ````python
        def evaluate_pandera_contract_parquet_files(
            parquet_paths: list[Path],
            *,
            schema_class: type[DataFrameModel],
        ) -> PanderaContractEvaluation:
            """Load one or more parquet files and validate them as a single staged dataset.

            Reads multiple Parquet files, concatenates them into a single DataFrame,
            and validates against the provided schema. This is useful when DLT
            produces multiple Parquet files for a single ingestion run.

            Args:
                parquet_paths: List of paths to Parquet files to validate.
                schema_class: Pandera DataFrameModel subclass defining validation rules.

            Returns:
                PanderaContractEvaluation: Combined result of the validation.

            Raises:
                FileNotFoundError: If parquet_paths is empty.

            Example:
                \```python
                from pathlib import Path
                from phlo_dlt.pandera_checks import evaluate_pandera_contract_parquet_files

                paths = [Path("/tmp/part1.parquet"), Path("/tmp/part2.parquet")]
                result = evaluate_pandera_contract_parquet_files(
                    paths,
                    schema_class=UserSchema,
                )
                \```

            See Also:
                :func:`evaluate_pandera_contract_parquet`: For single file validation.

            """
            if not parquet_paths:
                raise FileNotFoundError("Missing parquet_paths in ingestion metadata")
            frames = [pd.read_parquet(parquet_path) for parquet_path in parquet_paths]
            return evaluate_pandera_contract(
                pd.concat(frames, ignore_index=True), schema_class=schema_class
            )
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;parquet_paths&#x22;" type="&#x22;list[Path]&#x22;" value="undefined">
          List of paths to Parquet files to validate.
        </PyParameter>

        <PyParameter name="&#x22;schema_class&#x22;" type="&#x22;type[DataFrameModel]&#x22;" value="undefined">
          Pandera DataFrameModel subclass defining validation rules.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_dlt.pandera_checks.PanderaContractEvaluation&#x22;">
        Combined result of the validation.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;evaluate_pandera_contract&#x22;" type="&#x22;(df, *, schema_class) -> PanderaContractEvaluation&#x22;">
      Validate a dataframe against a Pandera schema class.

      Performs comprehensive validation of a pandas DataFrame against a
      Pandera schema. Handles datetime coercion, nullable column defaults,
      and provides detailed failure information.

      <Callout title="&#x22;Validation Steps&#x22;" type="&#x22;validation-steps&#x22;">
        1. Add null columns for missing nullable fields
        2. Coerce datetime columns to proper type
        3. Run Pandera validation
        4. Capture any SchemaErrors or exceptions
      </Callout>

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        import pandas as pd
        from phlo_dlt.pandera_checks import evaluate_pandera_contract

        df = pd.DataFrame(\{"id": [1, 2, 3], "name": ["a", "b", "c"]\})
        result = evaluate_pandera_contract(df, schema_class=UserSchema)
        ```
      </Callout>

      <PySourceCode>
        ````python
        def evaluate_pandera_contract(
            df: pd.DataFrame,
            *,
            schema_class: type[DataFrameModel],
        ) -> PanderaContractEvaluation:
            """Validate a dataframe against a Pandera schema class.

            Performs comprehensive validation of a pandas DataFrame against a
            Pandera schema. Handles datetime coercion, nullable column defaults,
            and provides detailed failure information.

            Args:
                df: pandas DataFrame to validate.
                schema_class: Pandera DataFrameModel subclass defining validation rules.

            Returns:
                PanderaContractEvaluation: Detailed validation result.

            Validation Steps:
                1. Add null columns for missing nullable fields
                2. Coerce datetime columns to proper type
                3. Run Pandera validation
                4. Capture any SchemaErrors or exceptions

            Example:
                \```python
                import pandas as pd
                from phlo_dlt.pandera_checks import evaluate_pandera_contract

                df = pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})
                result = evaluate_pandera_contract(df, schema_class=UserSchema)
                \```

            """
            schema = schema_class.to_schema()
            validated_df = df
            for column_name, column in schema.columns.items():
                if column_name in validated_df.columns or not column.nullable:
                    continue
                validated_df = df.copy()
                validated_df[column_name] = None
                break
            for column_name, column in schema.columns.items():
                if column_name in validated_df.columns or not column.nullable:
                    continue
                validated_df[column_name] = None

            datetime_columns = [
                name
                for name, column in schema.columns.items()
                if isinstance(column.dtype, pandas_engine.DateTime)
            ]
            for column_name in datetime_columns:
                if column_name not in validated_df.columns:
                    continue
                series = validated_df[column_name]
                if pd.api.types.is_datetime64_any_dtype(series):
                    continue
                if not (pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series)):
                    continue
                try:
                    if validated_df is df:
                        validated_df = df.copy()
                    validated_df[column_name] = pd.to_datetime(series)
                except (ValueError, TypeError):
                    pass

            try:
                schema_class.validate(validated_df, lazy=True)
            except pandera.errors.SchemaErrors as err:
                failure_cases = err.failure_cases
                sample = failure_cases.head(20).to_dict(orient="records")
                return PanderaContractEvaluation(
                    passed=False,
                    failed_count=len(failure_cases),
                    total_count=len(validated_df),
                    sample=sample,
                    error=str(err),
                )
            except Exception as exc:  # noqa: BLE001 - surface validation errors in check metadata
                return PanderaContractEvaluation(
                    passed=False,
                    failed_count=1,
                    total_count=len(validated_df),
                    sample=[{"error": str(exc)}],
                    error=str(exc),
                )

            return PanderaContractEvaluation(
                passed=True,
                failed_count=0,
                total_count=len(df),
                sample=[],
            )
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;df&#x22;" type="&#x22;pd.DataFrame&#x22;" value="undefined">
          pandas DataFrame to validate.
        </PyParameter>

        <PyParameter name="&#x22;schema_class&#x22;" type="&#x22;type[DataFrameModel]&#x22;" value="undefined">
          Pandera DataFrameModel subclass defining validation rules.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_dlt.pandera_checks.PanderaContractEvaluation&#x22;">
        Detailed validation result.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;pandera_contract_asset_check_result&#x22;" type="&#x22;(evaluation, *, partition_key, asset_key, schema_class, query_or_sql) -> CheckResult&#x22;">
      Build a normalized Phlo check result from Pandera evaluation output.

      Converts a PanderaContractEvaluation into a Phlo CheckResult that can
      be consumed by the Phlo orchestrator and displayed in the UI.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        from phlo_dlt.pandera_checks import (
            evaluate_pandera_contract_parquet,
            pandera_contract_asset_check_result,
        )

        evaluation = evaluate_pandera_contract_parquet(path, schema_class=MySchema)
        check_result = pandera_contract_asset_check_result(
            evaluation,
            partition_key="2024-01-01",
            asset_key="dlt_users",
            schema_class=MySchema,
            query_or_sql="parquet:///tmp/data.parquet",
        )
        ```
      </Callout>

      <PySourceCode>
        ````python
        def pandera_contract_asset_check_result(
            evaluation: PanderaContractEvaluation,
            *,
            partition_key: str | None,
            asset_key: str,
            schema_class: type[DataFrameModel],
            query_or_sql: str,
        ) -> CheckResult:
            """Build a normalized Phlo check result from Pandera evaluation output.

            Converts a PanderaContractEvaluation into a Phlo CheckResult that can
            be consumed by the Phlo orchestrator and displayed in the UI.

            Args:
                evaluation: The Pandera validation evaluation to convert.
                partition_key: Optional partition key for the check context.
                asset_key: Asset identifier (e.g., "dlt_users").
                schema_class: Pandera schema class used for validation.
                query_or_sql: Query string or SQL describing the data source.

            Returns:
                CheckResult: Normalized Phlo check result.

            Example:
                \```python
                from phlo_dlt.pandera_checks import (
                    evaluate_pandera_contract_parquet,
                    pandera_contract_asset_check_result,
                )

                evaluation = evaluate_pandera_contract_parquet(path, schema_class=MySchema)
                check_result = pandera_contract_asset_check_result(
                    evaluation,
                    partition_key="2024-01-01",
                    asset_key="dlt_users",
                    schema_class=MySchema,
                    query_or_sql="parquet:///tmp/data.parquet",
                )
                \```

            """
            metadata: dict[str, Any] = {
                "source": "pandera",
                "partition_key": partition_key,
                "failed_count": evaluation.failed_count,
                "total_count": evaluation.total_count,
                "query_or_sql": query_or_sql,
                "sample": evaluation.sample[:20],
                "schema": schema_class.__name__,
            }
            if evaluation.error:
                metadata["error"] = evaluation.error

            return CheckResult(
                passed=evaluation.passed,
                check_name=PANDERA_CONTRACT_CHECK_NAME,
                metadata=metadata,
                severity=None if evaluation.passed else "error",
                asset_key=asset_key,
            )
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;evaluation&#x22;" type="&#x22;PanderaContractEvaluation&#x22;" value="undefined">
          The Pandera validation evaluation to convert.
        </PyParameter>

        <PyParameter name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Optional partition key for the check context.
        </PyParameter>

        <PyParameter name="&#x22;asset_key&#x22;" type="&#x22;str&#x22;" value="undefined">
          Asset identifier (e.g., "dlt\_users").
        </PyParameter>

        <PyParameter name="&#x22;schema_class&#x22;" type="&#x22;type[DataFrameModel]&#x22;" value="undefined">
          Pandera schema class used for validation.
        </PyParameter>

        <PyParameter name="&#x22;query_or_sql&#x22;" type="&#x22;str&#x22;" value="undefined">
          Query string or SQL describing the data source.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo.capabilities.specs.CheckResult&#x22;">
        Normalized Phlo check result.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;serialize_pandera_contract_evaluation&#x22;" type="&#x22;(evaluation) -> dict[str, Any]&#x22;">
      Convert a Pandera contract evaluation to metadata-safe primitives.

      Serializes the evaluation for storage in ingestion metadata, allowing
      results to be passed between pipeline stages or stored for auditing.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        evaluation = PanderaContractEvaluation(
            passed=True, failed_count=0, total_count=100, sample=[], error=None
        )
        metadata = serialize_pandera_contract_evaluation(evaluation)
        # Can now be stored in JSON/YAML metadata
        ```
      </Callout>

      <Callout title="&#x22;See Also&#x22;" type="&#x22;see-also&#x22;">
        :func:`deserialize_pandera_contract_evaluation`: Reverse operation.
      </Callout>

      <PySourceCode>
        ````python
        def serialize_pandera_contract_evaluation(
            evaluation: PanderaContractEvaluation,
        ) -> dict[str, Any]:
            """Convert a Pandera contract evaluation to metadata-safe primitives.

            Serializes the evaluation for storage in ingestion metadata, allowing
            results to be passed between pipeline stages or stored for auditing.

            Args:
                evaluation: The evaluation to serialize.

            Returns:
                dict[str, Any]: Dictionary with primitive values suitable for metadata.

            Example:
                \```python
                evaluation = PanderaContractEvaluation(
                    passed=True, failed_count=0, total_count=100, sample=[], error=None
                )
                metadata = serialize_pandera_contract_evaluation(evaluation)
                # Can now be stored in JSON/YAML metadata
                \```

            See Also:
                :func:`deserialize_pandera_contract_evaluation`: Reverse operation.

            """
            return {
                "passed": evaluation.passed,
                "failed_count": evaluation.failed_count,
                "total_count": evaluation.total_count,
                "sample": evaluation.sample,
                "error": evaluation.error,
            }
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;evaluation&#x22;" type="&#x22;PanderaContractEvaluation&#x22;" value="undefined">
          The evaluation to serialize.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        dict\[str, Any]: Dictionary with primitive values suitable for metadata.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;deserialize_pandera_contract_evaluation&#x22;" type="&#x22;(payload) -> PanderaContractEvaluation | None&#x22;">
      Convert metadata payload back into a Pandera contract evaluation.

      Deserializes an evaluation from metadata storage. Handles type coercion
      and validation of the payload structure.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        metadata = \{"passed": True, "failed_count": 0, "total_count": 100, "sample": []\}
        evaluation = deserialize_pandera_contract_evaluation(metadata)
        if evaluation:
            print(f"Validation passed: \{evaluation.passed\}")
        ```
      </Callout>

      <Callout title="&#x22;See Also&#x22;" type="&#x22;see-also&#x22;">
        :func:`serialize_pandera_contract_evaluation`: Forward operation.
      </Callout>

      <PySourceCode>
        ````python
        def deserialize_pandera_contract_evaluation(payload: Any) -> PanderaContractEvaluation | None:
            """Convert metadata payload back into a Pandera contract evaluation.

            Deserializes an evaluation from metadata storage. Handles type coercion
            and validation of the payload structure.

            Args:
                payload: Dictionary from metadata storage, typically from
                    :func:`serialize_pandera_contract_evaluation`.

            Returns:
                PanderaContractEvaluation | None: The deserialized evaluation, or None
                if payload is not a valid dictionary.

            Example:
                \```python
                metadata = {"passed": True, "failed_count": 0, "total_count": 100, "sample": []}
                evaluation = deserialize_pandera_contract_evaluation(metadata)
                if evaluation:
                    print(f"Validation passed: {evaluation.passed}")
                \```

            See Also:
                :func:`serialize_pandera_contract_evaluation`: Forward operation.

            """
            if not isinstance(payload, dict):
                return None
            sample = payload.get("sample")
            return PanderaContractEvaluation(
                passed=bool(payload.get("passed")),
                failed_count=int(payload.get("failed_count", 0)),
                total_count=int(payload.get("total_count", 0)),
                sample=sample if isinstance(sample, list) else [],
                error=str(payload["error"]) if payload.get("error") is not None else None,
            )
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;payload&#x22;" type="&#x22;Any&#x22;" value="undefined">
          Dictionary from metadata storage, typically from
          :func:`serialize_pandera_contract_evaluation`.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;PanderaContractEvaluation | None&#x22;">
        PanderaContractEvaluation | None: The deserialized evaluation, or None
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
