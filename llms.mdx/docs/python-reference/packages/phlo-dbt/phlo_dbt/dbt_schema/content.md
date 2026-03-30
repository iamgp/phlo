# dbt_schema (/docs/python-reference/packages/phlo-dbt/phlo_dbt/dbt_schema)



Generate Pandera schemas from dbt model YAML files.

Enables single source of truth: define schema in dbt model YAML,
generate Pandera schema automatically.

This module bridges dbt and Pandera by parsing dbt model YAML files and
generating corresponding Pandera DataFrameModel classes. This enables
data validation using the same schema definitions used for documentation
and testing in dbt.

Example:

> > > from phlo\_dbt.dbt\_schema import dbt\_model\_to\_pandera
> > > Schema = dbt\_model\_to\_pandera(
> > > ...     "workflows/transforms/dbt/models/silver/fct\_orders.yml",
> > > ...     "fct\_orders"
> > > ... )
> > >
> > > Use for validation [#use-for-validation]
> > >
> > > import pandas as pd
> > > df = pd.read\_csv("orders.csv")
> > > validated\_df = Schema.validate(df)
> > >
> > > Schema can also be used with Phlo's quality checks [#schema-can-also-be-used-with-phlos-quality-checks]
> > >
> > > from phlo.quality import phlo\_quality
> > > @phlo\_quality(schema=Schema)
> > > ... def load\_orders():
> > > ...     return df

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;PhloSchema&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dbt/phlo_dbt/dbt_schema/PhloSchema&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_parse_dbt_tests&#x22;" type="&#x22;(data_tests) -> dict[str, Any]&#x22;">
      Parse dbt data\_tests into Pandera Field kwargs.

      <PySourceCode>
        ```python
        def _parse_dbt_tests(data_tests: list[Any]) -> dict[str, Any]:
            """Parse dbt data_tests into Pandera Field kwargs."""
            kwargs: dict[str, Any] = {}
            accepted_values: list[Any] | None = None

            for test in data_tests:
                if isinstance(test, str):
                    # Simple test like "not_null" or "unique"
                    if test == "not_null":
                        kwargs["nullable"] = False
                    elif test == "unique":
                        kwargs["unique"] = True
                elif isinstance(test, dict):
                    # Complex test with config
                    for test_name, test_config in test.items():
                        if test_name == "accepted_values":
                            accepted_values = test_config.get("values", [])
                        elif test_name == "dbt_expectations.expect_column_values_to_be_between":
                            if "min_value" in test_config:
                                kwargs["ge"] = test_config["min_value"]
                            if "max_value" in test_config:
                                kwargs["le"] = test_config["max_value"]
                        elif test_name == "dbt_utils.accepted_range":
                            if "min_value" in test_config:
                                kwargs["ge"] = test_config["min_value"]
                            if "max_value" in test_config:
                                kwargs["le"] = test_config["max_value"]

            if accepted_values is not None:
                kwargs["isin"] = accepted_values

            return kwargs
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;data_tests&#x22;" type="&#x22;list[Any]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_infer_type&#x22;" type="&#x22;(column_name, data_tests) -> type&#x22;">
      Infer Python type from column name and tests.

      dbt doesn't have explicit types in model YAML (they're in the SQL),
      so we use heuristics based on column names and test values.

      <PySourceCode>
        ```python
        def _infer_type(column_name: str, data_tests: list[Any]) -> type:
            """Infer Python type from column name and tests.

            dbt doesn't have explicit types in model YAML (they're in the SQL),
            so we use heuristics based on column names and test values.
            """
            name_lower = column_name.lower()

            # Timestamp patterns
            if "timestamp" in name_lower or "date" in name_lower or name_lower.endswith("_at"):
                return datetime

            # Check accepted_values for type hints
            for test in data_tests:
                if isinstance(test, dict):
                    if "accepted_values" in test:
                        values = test["accepted_values"].get("values", [])
                        if values and all(isinstance(v, int) for v in values):
                            return int
                        if values and all(isinstance(v, str) for v in values):
                            return str
                    if "dbt_expectations.expect_column_values_to_be_between" in test:
                        config = test["dbt_expectations.expect_column_values_to_be_between"]
                        if isinstance(config.get("min_value"), int):
                            return int
                        if isinstance(config.get("min_value"), float):
                            return float

            # ID patterns
            if name_lower.endswith("_id") or name_lower == "id":
                return str

            # Numeric patterns
            if any(x in name_lower for x in ["count", "amount", "num", "qty", "pct", "percent"]):
                if "pct" in name_lower or "percent" in name_lower:
                    return float
                return int

            # Default to string
            return str
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;column_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;data_tests&#x22;" type="&#x22;list[Any]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;type&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;dbt_model_to_pandera&#x22;" type="&#x22;(yaml_path, model_name, class_name=None) -> type[PhloSchema]&#x22;">
      Generate a PhloSchema class from a dbt model YAML file.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        Schema = dbt\_model\_to\_pandera(
        "workflows/transforms/dbt/models/silver/fct\_orders.yml",
        "fct\_orders"
        )
        validated\_df = Schema.validate(df)
      </Callout>

      <PySourceCode>
        ```python
        def dbt_model_to_pandera(
            yaml_path: str | Path,
            model_name: str,
            class_name: str | None = None,
        ) -> type[PhloSchema]:
            """Generate a PhloSchema class from a dbt model YAML file.

            Args:
                yaml_path: Path to the dbt model YAML file
                model_name: Name of the model in the YAML (e.g., "fct_orders")
                class_name: Optional class name (defaults to PascalCase of model_name)

            Returns:
                A dynamically created PhloSchema subclass

            Example:
                Schema = dbt_model_to_pandera(
                    "workflows/transforms/dbt/models/silver/fct_orders.yml",
                    "fct_orders"
                )
                validated_df = Schema.validate(df)

            """
            yaml_path = Path(yaml_path)
            configured_column_count: int | None = None
            generated_column_count = 0
            logger.info(
                "dbt_schema_generation_started",
                yaml_path=str(yaml_path),
                model_name=model_name,
            )

            try:
                with open(yaml_path) as f:
                    dbt_config = yaml.safe_load(f)

                # Find the model in the YAML
                model_config = None
                for model in dbt_config.get("models", []):
                    if model.get("name") == model_name:
                        model_config = model
                        break

                if model_config is None:
                    raise ValueError(f"Model '{model_name}' not found in {yaml_path}")

                # Generate class name if not provided
                if class_name is None:
                    class_name = "".join(word.capitalize() for word in model_name.split("_"))

                # Build annotations and namespace
                annotations: dict[str, Any] = {}
                namespace: dict[str, Any] = {
                    "__annotations__": annotations,
                    "__module__": __name__,
                }

                columns = model_config.get("columns", [])
                if not isinstance(columns, list):
                    raise ValueError(f"Model '{model_name}' columns are not a list")
                configured_column_count = len(columns)

                for column in columns:
                    if not isinstance(column, dict):
                        continue
                    col_name = column.get("name")
                    if not isinstance(col_name, str):
                        continue
                    data_tests = column.get("data_tests", column.get("tests", []))

                    # Parse tests into Field kwargs
                    field_kwargs = _parse_dbt_tests(data_tests)

                    # Infer type
                    python_type = _infer_type(col_name, data_tests)

                    # Handle nullable
                    is_nullable = field_kwargs.pop("nullable", True)
                    if not is_nullable:
                        annotations[col_name] = python_type
                    else:
                        annotations[col_name] = python_type | None

                    # Create Field if there are constraints
                    if field_kwargs:
                        namespace[col_name] = Field(**field_kwargs)

                generated_column_count = len(annotations)

                # Create the class dynamically
                from typing import cast

                schema_class = cast(type[PhloSchema], type(class_name, (PhloSchema,), namespace))
                schema_class.__doc__ = model_config.get("description", f"Schema for {model_name}")
                logger.info(
                    "dbt_schema_generation_finished",
                    yaml_path=str(yaml_path),
                    model_name=model_name,
                    configured_column_count=configured_column_count,
                    generated_column_count=generated_column_count,
                )
                return schema_class
            except Exception as exc:
                logger.error(
                    "dbt_schema_generation_failed",
                    yaml_path=str(yaml_path),
                    model_name=model_name,
                    configured_column_count=configured_column_count,
                    generated_column_count=generated_column_count,
                    error=str(exc),
                    exc_info=True,
                )
                raise
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;yaml_path&#x22;" type="&#x22;str | Path&#x22;" value="undefined">
          Path to the dbt model YAML file
        </PyParameter>

        <PyParameter name="&#x22;model_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Name of the model in the YAML (e.g., "fct\_orders")
        </PyParameter>

        <PyParameter name="&#x22;class_name&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional class name (defaults to PascalCase of model\_name)
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;type&#x22;">
        A dynamically created PhloSchema subclass
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
