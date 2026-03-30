# type_mapping (/docs/python-reference/packages/phlo-trino/phlo_trino/type_mapping)



Schema-aware type mapping utilities for Trino to Pandas conversion.

Provides centralized Trino-to-Pandas type mappings and schema-aware
data loading to eliminate manual type conversion boilerplate.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<PyAttribute name="&#x22;TRINO_TO_PANDAS_TYPES&#x22;" type="&#x22;dict[str, str]&#x22;" value="&#x22;{'tinyint': 'int8', 'smallint': 'int16', 'integer': 'int32', 'bigint': 'int64', 'int': 'int64', 'real': 'float32', 'double': 'float64', 'float': 'float64', 'decimal': 'float64', 'varchar': 'string', 'char': 'string', 'string': 'string', 'json': 'string', 'boolean': 'bool', 'timestamp': 'datetime64[ns]', 'timestamp with time zone': 'datetime64[ns, UTC]', 'date': 'datetime64[ns]', 'time': 'string', 'varbinary': 'bytes', 'uuid': 'string'}&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;trino_type_to_pandas&#x22;" type="&#x22;(trino_type) -> str&#x22;">
      Convert a Trino data type to the corresponding Pandas dtype.

      <PySourceCode>
        ```python
        def trino_type_to_pandas(trino_type: str) -> str:
            """Convert a Trino data type to the corresponding Pandas dtype.

            Args:
                trino_type: Trino column type (e.g., "bigint", "varchar", "timestamp")

            Returns:
                Pandas dtype string (e.g., "int64", "string", "datetime64[ns]")

            Examples:
                >>> trino_type_to_pandas("bigint")
                'int64'
                >>> trino_type_to_pandas("varchar(255)")
                'string'
                >>> trino_type_to_pandas("timestamp")
                'datetime64[ns]'

            """
            # Normalize: lowercase and strip parameters like varchar(255)
            normalized = trino_type.lower().strip()
            if "(" in normalized:
                normalized = normalized.split("(")[0]

            return TRINO_TO_PANDAS_TYPES.get(normalized, "object")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;trino_type&#x22;" type="&#x22;str&#x22;" value="undefined">
          Trino column type (e.g., "bigint", "varchar", "timestamp")
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Pandas dtype string (e.g., "int64", "string", "datetime64\[ns]")
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;apply_schema_types&#x22;" type="&#x22;(df, schema_class) -> pd.DataFrame&#x22;">
      Apply types from a Pandera schema to a DataFrame.

      This eliminates manual type conversion code in quality checks.
      Uses the schema's type hints to coerce DataFrame columns.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        from phlo\_trino.type\_mapping import apply\_schema\_types
        from workflows.schemas.orders import FactOrders

        df = trino.query("SELECT \* FROM gold.fct\_orders")
        df = apply\_schema\_types(df, FactOrders)

        Types are now correct for validation [#types-are-now-correct-for-validation]
      </Callout>

      <PySourceCode>
        ```python
        def apply_schema_types(
            df: pd.DataFrame,
            schema_class: type[Any],
        ) -> pd.DataFrame:
            """Apply types from a Pandera schema to a DataFrame.

            This eliminates manual type conversion code in quality checks.
            Uses the schema's type hints to coerce DataFrame columns.

            Args:
                df: DataFrame to apply types to
                schema_class: Pandera DataFrameModel class with type annotations

            Returns:
                DataFrame with types coerced according to schema

            Example:
                from phlo_trino.type_mapping import apply_schema_types
                from workflows.schemas.orders import FactOrders

                df = trino.query("SELECT * FROM gold.fct_orders")
                df = apply_schema_types(df, FactOrders)
                # Types are now correct for validation

            """
            import types
            from typing import get_args, get_origin, get_type_hints

            hints = get_type_hints(schema_class)

            for col_name, type_hint in hints.items():
                if col_name not in df.columns:
                    continue

                # Handle Optional types (str | None -> str)
                origin = get_origin(type_hint)
                if origin is types.UnionType:
                    args = [a for a in get_args(type_hint) if a is not type(None)]
                    if args:
                        type_hint = args[0]

                # Apply type conversion based on Python type hint
                try:
                    if type_hint is int:
                        df[col_name] = pd.to_numeric(df[col_name], errors="coerce").astype("Int64")
                    elif type_hint is float:
                        df[col_name] = pd.to_numeric(df[col_name], errors="coerce")
                    elif type_hint is str:
                        df[col_name] = df[col_name].astype("string")
                    elif type_hint is bool:
                        df[col_name] = df[col_name].astype("boolean")
                    # datetime types are usually handled by Pandera coerce=True
                except Exception:
                    logger.debug("type_coercion_skipped", column=col_name, target_type=type_hint.__name__)

            return df
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;df&#x22;" type="&#x22;pd.DataFrame&#x22;" value="undefined">
          DataFrame to apply types to
        </PyParameter>

        <PyParameter name="&#x22;schema_class&#x22;" type="&#x22;type[Any]&#x22;" value="undefined">
          Pandera DataFrameModel class with type annotations
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;pandas.DataFrame&#x22;">
        DataFrame with types coerced according to schema
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
