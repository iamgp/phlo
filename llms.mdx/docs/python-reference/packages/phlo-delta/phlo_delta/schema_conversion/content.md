# schema_conversion (/docs/python-reference/packages/phlo-delta/phlo_delta/schema_conversion)



Pandera-to-Delta (PyArrow) schema conversion utilities.

This module provides functions to convert Pandera DataFrameModel schemas
to PyArrow schemas suitable for Delta Lake table creation. It handles
type mapping, metadata column injection, and validation.

Example:
from phlo\_delta.schema\_conversion import pandera\_to\_delta
from my\_schemas import EventSchema

arrow\_schema = pandera\_to\_delta(EventSchema)

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;SchemaConversionError&#x22;" href="&#x22;/docs/python-reference/packages/phlo-delta/phlo_delta/schema_conversion/SchemaConversionError&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;pandera_to_delta&#x22;" type="&#x22;(pandera_schema, add_dlt_metadata=True, add_phlo_metadata=True) -> pa.Schema&#x22;">
      Convert a Pandera DataFrameModel schema to a PyArrow schema for Delta Lake.

      Transforms Pandera field annotations and constraints into equivalent
      PyArrow types. Optionally injects DLT and Phlo metadata columns.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        from pandera.pandas import DataFrameModel
        from typing import Annotated
        import pandera as pa

        class EventSchema(DataFrameModel):
        event\_id: Annotated\[str, pa.Field(nullable=False)]
        timestamp: Annotated\[datetime, pa.Field(nullable=False)]

        arrow\_schema = pandera\_to\_delta(EventSchema)
      </Callout>

      <PySourceCode>
        ```python
        def pandera_to_delta(
            pandera_schema: type[DataFrameModel],
            add_dlt_metadata: bool = True,
            add_phlo_metadata: bool = True,
        ) -> pa.Schema:
            """Convert a Pandera DataFrameModel schema to a PyArrow schema for Delta Lake.

            Transforms Pandera field annotations and constraints into equivalent
            PyArrow types. Optionally injects DLT and Phlo metadata columns.

            Args:
                pandera_schema: Source Pandera model class with field annotations.
                add_dlt_metadata: Whether to append standard DLT metadata columns
                    (_dlt_load_id, _dlt_id).
                add_phlo_metadata: Whether to append standard Phlo metadata columns
                    (_phlo_row_id, _phlo_ingested_at, _phlo_partition_date, _phlo_run_id).

            Returns:
                pa.Schema: Equivalent PyArrow schema ready for Delta Lake table creation.

            Raises:
                SchemaConversionError: If conversion fails due to missing annotations,
                    type mapping failures, or invalid schema structure.

            Example:
                from pandera.pandas import DataFrameModel
                from typing import Annotated
                import pandera as pa

                class EventSchema(DataFrameModel):
                    event_id: Annotated[str, pa.Field(nullable=False)]
                    timestamp: Annotated[datetime, pa.Field(nullable=False)]

                arrow_schema = pandera_to_delta(EventSchema)

            """
            fields: list[pa.Field] = []
            user_field_count = 0
            logger.info(
                "delta_schema_conversion_started",
                schema_name=pandera_schema.__name__,
                add_dlt_metadata=add_dlt_metadata,
                add_phlo_metadata=add_phlo_metadata,
            )

            try:
                annotations = get_type_hints(pandera_schema)
            except Exception as e:
                logger.exception(
                    "delta_schema_conversion_type_hints_failed",
                    schema_name=pandera_schema.__name__,
                )
                raise SchemaConversionError(
                    f"Failed to get type hints from Pandera schema {pandera_schema.__name__}: {e}"
                ) from e

            if not annotations:
                logger.error(
                    "delta_schema_conversion_no_annotations",
                    schema_name=pandera_schema.__name__,
                )
                raise SchemaConversionError(
                    f"Pandera schema {pandera_schema.__name__} has no field annotations"
                )

            try:
                pandera_schema_obj = pandera_schema.to_schema()
            except Exception as e:
                logger.exception(
                    "delta_schema_conversion_schema_build_failed",
                    schema_name=pandera_schema.__name__,
                )
                raise SchemaConversionError(
                    f"Failed to instantiate Pandera schema {pandera_schema.__name__}: {e}"
                ) from e

            for field_name, field_type in annotations.items():
                if field_name.startswith("__") or field_name == "Config":
                    continue
                user_field_count += 1

                nullable = True
                if field_name in pandera_schema_obj.columns:
                    column = pandera_schema_obj.columns[field_name]
                    nullable = column.nullable

                try:
                    arrow_type = _map_type(field_name, field_type)
                except SchemaConversionError as e:
                    logger.warning(
                        "delta_schema_conversion_field_type_unsupported",
                        schema_name=pandera_schema.__name__,
                        field_name=field_name,
                    )
                    raise SchemaConversionError(
                        f"Cannot map Pandera type for field {field_name}: {e}"
                    ) from e

                fields.append(pa.field(field_name, arrow_type, nullable=nullable))

            if user_field_count == 0:
                logger.error(
                    "delta_schema_conversion_no_fields",
                    schema_name=pandera_schema.__name__,
                )
                raise SchemaConversionError(f"No fields found in Pandera schema {pandera_schema.__name__}")

            if add_dlt_metadata:
                existing_names = {f.name for f in fields}
                if "_dlt_load_id" not in existing_names:
                    fields.append(pa.field("_dlt_load_id", pa.string(), nullable=False))
                if "_dlt_id" not in existing_names:
                    fields.append(pa.field("_dlt_id", pa.string(), nullable=False))

            if add_phlo_metadata:
                existing_names = {f.name for f in fields}
                if "_phlo_row_id" not in existing_names:
                    fields.append(pa.field("_phlo_row_id", pa.string(), nullable=False))
                if "_phlo_ingested_at" not in existing_names:
                    fields.append(
                        pa.field("_phlo_ingested_at", pa.timestamp("us", tz="UTC"), nullable=False)
                    )
                if "_phlo_partition_date" not in existing_names:
                    fields.append(pa.field("_phlo_partition_date", pa.string(), nullable=False))
                if "_phlo_run_id" not in existing_names:
                    fields.append(pa.field("_phlo_run_id", pa.string(), nullable=False))

            logger.info(
                "delta_schema_conversion_finished",
                schema_name=pandera_schema.__name__,
                total_field_count=len(fields),
                user_field_count=user_field_count,
            )
            return pa.schema(fields)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;pandera_schema&#x22;" type="&#x22;type[DataFrameModel]&#x22;" value="undefined">
          Source Pandera model class with field annotations.
        </PyParameter>

        <PyParameter name="&#x22;add_dlt_metadata&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
          Whether to append standard DLT metadata columns
          (\_dlt\_load\_id, \_dlt\_id).
        </PyParameter>

        <PyParameter name="&#x22;add_phlo_metadata&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
          Whether to append standard Phlo metadata columns
          (\_phlo\_row\_id, \_phlo\_ingested\_at, \_phlo\_partition\_date, \_phlo\_run\_id).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;pyarrow.Schema&#x22;">
        pa.Schema: Equivalent PyArrow schema ready for Delta Lake table creation.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_map_type&#x22;" type="&#x22;(field_name, pandera_type) -> pa.DataType&#x22;">
      Map a Pandera-annotated type to a PyArrow type.

      Handles complex types (Optional, List, Dict) and delegates scalar
      types to \_map\_scalar. Rejects unsupported container types.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        arrow\_type = \_map\_type("user\_id", str)

        Returns: pa.string() [#returns-pastring]
      </Callout>

      <PySourceCode>
        ```python
        def _map_type(field_name: str, pandera_type: Any) -> pa.DataType:
            """Map a Pandera-annotated type to a PyArrow type.

            Handles complex types (Optional, List, Dict) and delegates scalar
            types to _map_scalar. Rejects unsupported container types.

            Args:
                field_name: Source field name for error reporting.
                pandera_type: Annotated Python/Pandera type.

            Returns:
                pa.DataType: Corresponding PyArrow data type.

            Raises:
                SchemaConversionError: If type cannot be represented in PyArrow/Delta.

            Example:
                arrow_type = _map_type("user_id", str)
                # Returns: pa.string()

            """
            origin = get_origin(pandera_type)
            if origin is None:
                return _map_scalar(field_name, pandera_type)

            if origin is list:
                raise SchemaConversionError(f"Lists are not supported for field {field_name}")

            if origin is dict:
                raise SchemaConversionError(f"Dicts are not supported for field {field_name}")

            if origin is Any:
                return pa.string()

            if origin is type(None):
                return pa.string()

            args = get_args(pandera_type)
            for arg in args:
                if arg is type(None):
                    continue
                return _map_type(field_name, arg)

            return pa.string()
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;field_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Source field name for error reporting.
        </PyParameter>

        <PyParameter name="&#x22;pandera_type&#x22;" type="&#x22;Any&#x22;" value="undefined">
          Annotated Python/Pandera type.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;pyarrow.DataType&#x22;">
        pa.DataType: Corresponding PyArrow data type.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_map_scalar&#x22;" type="&#x22;(field_name, t) -> pa.DataType&#x22;">
      Map a scalar Python type to a PyArrow type.

      Converts basic Python types to their PyArrow equivalents for
      Delta Lake storage.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        arrow\_type = \_map\_scalar("price", float)

        Returns: pa.float64() [#returns-pafloat64]
      </Callout>

      <PySourceCode>
        ```python
        def _map_scalar(field_name: str, t: Any) -> pa.DataType:
            """Map a scalar Python type to a PyArrow type.

            Converts basic Python types to their PyArrow equivalents for
            Delta Lake storage.

            Args:
                field_name: Source field name for error reporting.
                t: Scalar Python type.

            Returns:
                pa.DataType: Corresponding PyArrow type.

            Raises:
                SchemaConversionError: If type is unsupported.

            Example:
                arrow_type = _map_scalar("price", float)
                # Returns: pa.float64()

            """
            if t in (str,):
                return pa.string()
            if t in (int,):
                return pa.int64()
            if t in (float,):
                return pa.float64()
            if t in (bool,):
                return pa.bool_()
            if t in (datetime,):
                return pa.timestamp("us", tz="UTC")
            if t in (date,):
                return pa.date32()
            if t in (bytes,):
                return pa.binary()
            if t in (Decimal,):
                return pa.float64()

            raise SchemaConversionError(f"Unsupported type for field {field_name}: {t}")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;field_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Source field name for error reporting.
        </PyParameter>

        <PyParameter name="&#x22;t&#x22;" type="&#x22;Any&#x22;" value="undefined">
          Scalar Python type.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;pyarrow.DataType&#x22;">
        pa.DataType: Corresponding PyArrow type.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
