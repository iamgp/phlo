# pandera_asset_checks (/docs/python-reference/packages/phlo-pandera/phlo_pandera/pandera_asset_checks)



Pandera contract evaluation and asset check utilities.

This module provides functions for evaluating Pandera schema contracts against
pandas DataFrames and parquet files. It handles schema validation, error collection,
and conversion to Phlo's standardized CheckResult format.

The module is designed to integrate Pandera's powerful schema validation with
Phlo's quality check framework, providing:

1. **Schema Evaluation**: Validate DataFrames against Pandera DataFrameModel classes
2. **Type Coercion**: Automatic datetime conversion for improved compatibility
3. **Parquet Support**: Load and validate parquet files directly
4. **Result Conversion**: Convert Pandera results to Phlo CheckResult format

Example:

```python
import pandas as pd
from pandera.pandas import DataFrameModel, Field
from phlo_pandera.pandera_asset_checks import (
    evaluate_pandera_contract,
    pandera_contract_asset_check_result,
)

class CustomerSchema(DataFrameModel):
    customer_id: int = Field(gt=0)
    email: str = Field(nullable=True)

# Validate a DataFrame
df = pd.DataFrame(\{
    "customer_id": [1, 2, 3],
    "email": ["alice@example.com", "bob@example.com", None],
\})

evaluation = evaluate_pandera_contract(df, schema_class=CustomerSchema)

# Convert to Phlo CheckResult
result = pandera_contract_asset_check_result(
    evaluation=evaluation,
    partition_key="2024-01-15",
    asset_key="customers",
    schema_class=CustomerSchema,
    query_or_sql="SELECT * FROM bronze.customers",
)
```

See Also:

* `checks_extra.py`: SchemaCheck class that uses these utilities
* `decorator.py`: `@phlo_pandera` decorator with Pandera integration
* `contract.py`: QualityCheckContract for metadata standardization

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;PanderaContractEvaluation&#x22;" href="&#x22;/docs/python-reference/packages/phlo-pandera/phlo_pandera/pandera_asset_checks/PanderaContractEvaluation&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;evaluate_pandera_contract&#x22;" type="&#x22;(df, *, schema_class) -> PanderaContractEvaluation&#x22;">
      Validate a DataFrame against a Pandera schema class.

      Performs schema validation using Pandera's lazy validation mode to collect
      all errors. Handles automatic datetime conversion for columns defined as
      datetime in the schema to improve compatibility.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        from pandera.pandas import DataFrameModel, Field

        class ProductSchema(DataFrameModel):
            product_id: int = Field(gt=0)
            price: float = Field(ge=0)

        df = pd.DataFrame(\{
            "product_id": [1, 2, -3],  # -3 fails gt=0 constraint
            "price": [9.99, -1.0, 5.0],  # -1.0 fails ge=0 constraint
        \})

        evaluation = evaluate_pandera_contract(df, schema_class=ProductSchema)
        # evaluation.passed == False
        # evaluation.failed_count >= 2
        ```
      </Callout>

      <PySourceCode>
        ````python
        def evaluate_pandera_contract(
            df: pd.DataFrame,
            *,
            schema_class: type[DataFrameModel],
        ) -> PanderaContractEvaluation:
            """Validate a DataFrame against a Pandera schema class.

            Performs schema validation using Pandera's lazy validation mode to collect
            all errors. Handles automatic datetime conversion for columns defined as
            datetime in the schema to improve compatibility.

            Args:
                df: Input DataFrame to validate. Must contain columns matching the
                    schema definition.
                schema_class: Pandera ``DataFrameModel`` class (not an instance) that
                    defines the expected structure and constraints.

            Returns:
                PanderaContractEvaluation with pass/fail status, failure counts,
                and sampled failure details.

            Raises:
                Exception: Catches and logs unexpected errors, returning failed evaluation.

            Example:
                \```python
                from pandera.pandas import DataFrameModel, Field

                class ProductSchema(DataFrameModel):
                    product_id: int = Field(gt=0)
                    price: float = Field(ge=0)

                df = pd.DataFrame({
                    "product_id": [1, 2, -3],  # -3 fails gt=0 constraint
                    "price": [9.99, -1.0, 5.0],  # -1.0 fails ge=0 constraint
                })

                evaluation = evaluate_pandera_contract(df, schema_class=ProductSchema)
                # evaluation.passed == False
                # evaluation.failed_count >= 2
                \```

            """

            schema = schema_class.to_schema()
            datetime_columns = [
                name
                for name, column in schema.columns.items()
                if isinstance(column.dtype, pandas_engine.DateTime)
            ]
            for column_name in datetime_columns:
                if column_name not in df.columns:
                    continue
                series = df[column_name]
                if pd.api.types.is_datetime64_any_dtype(series):
                    continue
                if not (pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series)):
                    continue
                try:
                    df[column_name] = pd.to_datetime(series)
                except (ValueError, TypeError):
                    pass

            try:
                schema_class.validate(df, lazy=True)
            except pandera.errors.SchemaErrors as err:
                failure_cases = err.failure_cases
                sample = failure_cases.head(20).to_dict(orient="records")
                return PanderaContractEvaluation(
                    passed=False,
                    failed_count=len(failure_cases),
                    total_count=len(df),
                    sample=sample,
                    error=str(err),
                )
            except Exception as exc:
                logger.exception(
                    "pandera_contract_evaluation_failed",
                    schema_name=schema_class.__name__,
                    total_count=len(df),
                )
                return PanderaContractEvaluation(
                    passed=False,
                    failed_count=1,
                    total_count=len(df),
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
          Input DataFrame to validate. Must contain columns matching the
          schema definition.
        </PyParameter>

        <PyParameter name="&#x22;schema_class&#x22;" type="&#x22;type[DataFrameModel]&#x22;" value="undefined">
          Pandera `DataFrameModel` class (not an instance) that
          defines the expected structure and constraints.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_pandera.pandera_asset_checks.PanderaContractEvaluation&#x22;">
        PanderaContractEvaluation with pass/fail status, failure counts,
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;evaluate_pandera_contract_parquet&#x22;" type="&#x22;(parquet_path, *, schema_class) -> PanderaContractEvaluation&#x22;">
      Load parquet data and validate it against a Pandera schema class.

      Convenience function that loads a parquet file into a DataFrame and
      immediately validates it against the provided schema.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        from pathlib import Path

        path = Path("data/products.parquet")
        evaluation = evaluate_pandera_contract_parquet(
            parquet_path=path,
            schema_class=ProductSchema,
        )
        ```
      </Callout>

      <PySourceCode>
        ````python
        def evaluate_pandera_contract_parquet(
            parquet_path: Path,
            *,
            schema_class: type[DataFrameModel],
        ) -> PanderaContractEvaluation:
            """Load parquet data and validate it against a Pandera schema class.

            Convenience function that loads a parquet file into a DataFrame and
            immediately validates it against the provided schema.

            Args:
                parquet_path: Path to the parquet file. Must exist and be readable.
                schema_class: Pandera ``DataFrameModel`` class defining the contract.

            Returns:
                PanderaContractEvaluation for the loaded DataFrame.

            Raises:
                Exception: Re-raises parquet read errors after logging them.

            Example:
                \```python
                from pathlib import Path

                path = Path("data/products.parquet")
                evaluation = evaluate_pandera_contract_parquet(
                    parquet_path=path,
                    schema_class=ProductSchema,
                )
                \```

            """

            try:
                df = pd.read_parquet(parquet_path)
            except Exception:
                logger.exception(
                    "pandera_contract_parquet_read_failed",
                    schema_name=schema_class.__name__,
                    parquet_path=str(parquet_path),
                )
                raise
            return evaluate_pandera_contract(df, schema_class=schema_class)
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;parquet_path&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Path to the parquet file. Must exist and be readable.
        </PyParameter>

        <PyParameter name="&#x22;schema_class&#x22;" type="&#x22;type[DataFrameModel]&#x22;" value="undefined">
          Pandera `DataFrameModel` class defining the contract.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_pandera.pandera_asset_checks.PanderaContractEvaluation&#x22;">
        PanderaContractEvaluation for the loaded DataFrame.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;pandera_contract_asset_check_result&#x22;" type="&#x22;(evaluation, *, partition_key, asset_key, schema_class, query_or_sql) -> CheckResult&#x22;">
      Build a Phlo quality check result from Pandera evaluation output.

      Converts a PanderaContractEvaluation into a standardized Phlo CheckResult
      with proper metadata, severity assignment, and contract information.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        evaluation = evaluate_pandera_contract(df, schema_class=CustomerSchema)

        result = pandera_contract_asset_check_result(
            evaluation=evaluation,
            partition_key="2024-01-15",
            asset_key="customers",
            schema_class=CustomerSchema,
            query_or_sql="SELECT * FROM bronze.customers",
        )

        # result.passed: bool
        # result.check_name: "pandera_contract"
        # result.severity: None if passed, "error" if failed
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
            """Build a Phlo quality check result from Pandera evaluation output.

            Converts a PanderaContractEvaluation into a standardized Phlo CheckResult
            with proper metadata, severity assignment, and contract information.

            Args:
                evaluation: Pandera contract evaluation summary from
                    ``evaluate_pandera_contract()``.
                partition_key: Optional partition key associated with the checked data,
                    typically in YYYY-MM-DD format.
                asset_key: Asset identifier for the check result (e.g., "customers").
                schema_class: Pandera schema class used for evaluation.
                query_or_sql: Query or SQL used to produce the evaluated dataset.

            Returns:
                Normalized CheckResult with metadata and severity appropriate for
                consumption by Dagster and the Observatory UI.

            Example:
                \```python
                evaluation = evaluate_pandera_contract(df, schema_class=CustomerSchema)

                result = pandera_contract_asset_check_result(
                    evaluation=evaluation,
                    partition_key="2024-01-15",
                    asset_key="customers",
                    schema_class=CustomerSchema,
                    query_or_sql="SELECT * FROM bronze.customers",
                )

                # result.passed: bool
                # result.check_name: "pandera_contract"
                # result.severity: None if passed, "error" if failed
                \```

            """

            contract = QualityCheckContract(
                source="pandera",
                partition_key=partition_key,
                failed_count=evaluation.failed_count,
                total_count=evaluation.total_count,
                query_or_sql=query_or_sql,
                repro_sql=None,
                sample=evaluation.sample,
            )
            metadata: dict[str, Any] = {
                **contract.to_metadata(),
                "schema": schema_class.__name__,
            }
            if evaluation.error:
                metadata["error"] = evaluation.error

            severity = severity_for_pandera_contract(passed=evaluation.passed)
            return CheckResult(
                passed=evaluation.passed,
                check_name=PANDERA_CONTRACT_CHECK_NAME,
                metadata=metadata,
                severity=severity,
                asset_key=asset_key,
            )
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;evaluation&#x22;" type="&#x22;PanderaContractEvaluation&#x22;" value="undefined">
          Pandera contract evaluation summary from
          `evaluate_pandera_contract()`.
        </PyParameter>

        <PyParameter name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Optional partition key associated with the checked data,
          typically in YYYY-MM-DD format.
        </PyParameter>

        <PyParameter name="&#x22;asset_key&#x22;" type="&#x22;str&#x22;" value="undefined">
          Asset identifier for the check result (e.g., "customers").
        </PyParameter>

        <PyParameter name="&#x22;schema_class&#x22;" type="&#x22;type[DataFrameModel]&#x22;" value="undefined">
          Pandera schema class used for evaluation.
        </PyParameter>

        <PyParameter name="&#x22;query_or_sql&#x22;" type="&#x22;str&#x22;" value="undefined">
          Query or SQL used to produce the evaluated dataset.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo.capabilities.specs.CheckResult&#x22;">
        Normalized CheckResult with metadata and severity appropriate for
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
