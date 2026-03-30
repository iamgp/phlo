# schema_conversion (/docs/python-reference/packages/phlo-iceberg/phlo_iceberg/schema_conversion)



Pandera-to-Iceberg schema conversion utilities.

This module provides utilities for converting Pandera DataFrameModel schemas
to PyIceberg Schema objects. It handles type mapping, metadata field injection,
and field ID assignment.

Supported type mappings:

* str -> StringType
* int -> LongType
* float -> DoubleType
* bool -> BooleanType
* datetime -> TimestamptzType
* date -> DateType
* bytes -> BinaryType
* Decimal -> DoubleType

The conversion automatically adds standard metadata columns for DLT and Phlo
traceability including `_dlt_load_id`, `_dlt_id`, `_phlo_ingested_at`,
`_phlo_row_id`, `_phlo_partition_date`, and `_phlo_run_id`.

Example:
Convert Pandera model to Iceberg schema::

from pandera import DataFrameModel, Column, Int64, String, Bool
from phlo\_iceberg.schema\_conversion import pandera\_to\_iceberg

class UserSchema(DataFrameModel):
id: Column\[Int64]
name: Column\[String]
active: Column\[Bool] = Field(nullable=True)

iceberg\_schema = pandera\_to\_iceberg(UserSchema)

Use with table creation [#use-with-table-creation]

from phlo\_iceberg import ensure\_table
table = ensure\_table("raw\.users", schema=iceberg\_schema)

See Also:
Pandera documentation: [https://pandera.readthedocs.io/](https://pandera.readthedocs.io/)
PyIceberg schema docs: [https://py.iceberg.apache.org/](https://py.iceberg.apache.org/)

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;SchemaConversionError&#x22;" href="&#x22;/docs/python-reference/packages/phlo-iceberg/phlo_iceberg/schema_conversion/SchemaConversionError&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;pandera_to_iceberg&#x22;" type="&#x22;(pandera_schema, start_field_id=1, add_dlt_metadata=True, add_phlo_metadata=True) -> Schema&#x22;">
      Convert a Pandera DataFrameModel schema to a PyIceberg Schema.

      Maps Pandera column types to Iceberg types, preserving nullability and
      descriptions. Automatically assigns field IDs and can inject standard
      metadata columns for data lineage.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        Basic conversion::

        from pandera import DataFrameModel, Column, Int64, String
        from phlo\_iceberg.schema\_conversion import pandera\_to\_iceberg

        class EventSchema(DataFrameModel):
        event\_id: Column\[Int64]
        event\_type: Column\[String]

        schema = pandera\_to\_iceberg(EventSchema)
        print(f"Schema has \{len(schema.fields)} fields")

        Conversion without metadata::

        schema = pandera\_to\_iceberg(
        EventSchema,
        add\_dlt\_metadata=False,
        add\_phlo\_metadata=False
        )

        Only has event_id and event_type fields [#only-has-event_id-and-event_type-fields]
      </Callout>

      <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
        Reserved field IDs 100-105 are used for metadata columns.
        User columns start from `start_field_id` and increment sequentially.
      </Callout>

      <PySourceCode>
        ```python
        def pandera_to_iceberg(
            pandera_schema: type[DataFrameModel],
            start_field_id: int = 1,
            add_dlt_metadata: bool = True,
            add_phlo_metadata: bool = True,
        ) -> Schema:
            """Convert a Pandera DataFrameModel schema to a PyIceberg Schema.

            Maps Pandera column types to Iceberg types, preserving nullability and
            descriptions. Automatically assigns field IDs and can inject standard
            metadata columns for data lineage.

            Args:
                pandera_schema: Pandera DataFrameModel class to convert.
                start_field_id: Starting field ID for user-defined columns (default: 1).
                    Metadata columns use reserved IDs 100-105.
                add_dlt_metadata: Whether to add DLT metadata columns
                    (``_dlt_load_id``, ``_dlt_id``).
                add_phlo_metadata: Whether to add Phlo metadata columns
                    (``_phlo_ingested_at``, ``_phlo_row_id``, ``_phlo_partition_date``,
                    ``_phlo_run_id``).

            Returns:
                Schema: Equivalent Iceberg schema with all fields and metadata.

            Raises:
                SchemaConversionError: If conversion fails due to unsupported types,
                    missing annotations, or invalid schema structure.

            Example:
                Basic conversion::

                    from pandera import DataFrameModel, Column, Int64, String
                    from phlo_iceberg.schema_conversion import pandera_to_iceberg

                    class EventSchema(DataFrameModel):
                        event_id: Column[Int64]
                        event_type: Column[String]

                    schema = pandera_to_iceberg(EventSchema)
                    print(f"Schema has {len(schema.fields)} fields")

                Conversion without metadata::

                    schema = pandera_to_iceberg(
                        EventSchema,
                        add_dlt_metadata=False,
                        add_phlo_metadata=False
                    )
                    # Only has event_id and event_type fields

            Note:
                Reserved field IDs 100-105 are used for metadata columns.
                User columns start from ``start_field_id`` and increment sequentially.

            """
            reserved_field_ids: dict[str, int] = {
                "_dlt_load_id": 100,
                "_dlt_id": 101,
                "_phlo_ingested_at": 102,
                "_phlo_row_id": 103,
                "_phlo_partition_date": 104,
                "_phlo_run_id": 105,
            }
            fields: list[NestedField] = []
            next_field_id = start_field_id
            user_field_count = 0
            logger.info(
                "iceberg_schema_conversion_started",
                schema_name=pandera_schema.__name__,
                start_field_id=start_field_id,
                add_dlt_metadata=add_dlt_metadata,
                add_phlo_metadata=add_phlo_metadata,
            )

            try:
                annotations = get_type_hints(pandera_schema)
            except Exception as e:
                logger.exception(
                    "iceberg_schema_conversion_type_hints_failed",
                    schema_name=pandera_schema.__name__,
                )
                raise SchemaConversionError(
                    f"Failed to get type hints from Pandera schema {pandera_schema.__name__}: {e}"
                ) from e

            if not annotations:
                logger.error(
                    "iceberg_schema_conversion_no_annotations",
                    schema_name=pandera_schema.__name__,
                )
                raise SchemaConversionError(
                    f"Pandera schema {pandera_schema.__name__} has no field annotations"
                )

            try:
                pandera_schema_obj = pandera_schema.to_schema()
            except Exception as e:
                logger.exception(
                    "iceberg_schema_conversion_schema_build_failed",
                    schema_name=pandera_schema.__name__,
                )
                raise SchemaConversionError(
                    f"Failed to instantiate Pandera schema {pandera_schema.__name__}: {e}"
                ) from e

            for field_name, field_type in annotations.items():
                if field_name.startswith("__") or field_name == "Config":
                    continue
                user_field_count += 1

                description = ""
                nullable = True

                if field_name in pandera_schema_obj.columns:
                    column = pandera_schema_obj.columns[field_name]
                    nullable = column.nullable
                    description = column.description or ""

                try:
                    iceberg_type = _map_type(field_name, field_type)
                except SchemaConversionError as e:
                    logger.warning(
                        "iceberg_schema_conversion_field_type_unsupported",
                        schema_name=pandera_schema.__name__,
                        field_name=field_name,
                    )
                    raise SchemaConversionError(
                        f"Cannot map Pandera type for field {field_name}: {e}"
                    ) from e

                field_id = reserved_field_ids.get(field_name, next_field_id)
                if field_name not in reserved_field_ids:
                    next_field_id += 1

                fields.append(
                    NestedField(
                        field_id=field_id,
                        name=field_name,
                        field_type=iceberg_type,
                        required=not nullable,
                        doc=description,
                    )
                )

            if user_field_count == 0:
                logger.error(
                    "iceberg_schema_conversion_no_fields",
                    schema_name=pandera_schema.__name__,
                )
                raise SchemaConversionError(f"No fields found in Pandera schema {pandera_schema.__name__}")

            if add_dlt_metadata:
                existing_names = {f.name for f in fields}
                if "_dlt_load_id" not in existing_names:
                    fields.append(
                        NestedField(
                            field_id=100,
                            name="_dlt_load_id",
                            field_type=StringType(),
                            required=True,
                            doc="DLT load identifier",
                        )
                    )
                if "_dlt_id" not in existing_names:
                    fields.append(
                        NestedField(
                            field_id=101,
                            name="_dlt_id",
                            field_type=StringType(),
                            required=True,
                            doc="DLT record identifier",
                        )
                    )

            if add_phlo_metadata:
                existing_names = {f.name for f in fields}
                if "_phlo_row_id" not in existing_names:
                    fields.append(
                        NestedField(
                            field_id=103,
                            name="_phlo_row_id",
                            field_type=StringType(),
                            required=True,
                            doc="Phlo row-level lineage identifier (ULID)",
                        )
                    )
                if "_phlo_ingested_at" not in existing_names:
                    fields.append(
                        NestedField(
                            field_id=102,
                            name="_phlo_ingested_at",
                            field_type=TimestamptzType(),
                            required=True,
                            doc="UTC timestamp when phlo processed this record",
                        )
                    )
                if "_phlo_partition_date" not in existing_names:
                    fields.append(
                        NestedField(
                            field_id=104,
                            name="_phlo_partition_date",
                            field_type=StringType(),
                            required=True,
                            doc="Partition date used for ingestion (YYYY-MM-DD)",
                        )
                    )
                if "_phlo_run_id" not in existing_names:
                    fields.append(
                        NestedField(
                            field_id=105,
                            name="_phlo_run_id",
                            field_type=StringType(),
                            required=True,
                            doc="Dagster run ID for traceability",
                        )
                    )

            logger.info(
                "iceberg_schema_conversion_finished",
                schema_name=pandera_schema.__name__,
                total_field_count=len(fields),
                user_field_count=user_field_count,
            )
            return Schema(*fields)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;pandera_schema&#x22;" type="&#x22;type[DataFrameModel]&#x22;" value="undefined">
          Pandera DataFrameModel class to convert.
        </PyParameter>

        <PyParameter name="&#x22;start_field_id&#x22;" type="&#x22;int&#x22;" value="&#x22;1&#x22;">
          Starting field ID for user-defined columns (default: 1).
          Metadata columns use reserved IDs 100-105.
        </PyParameter>

        <PyParameter name="&#x22;add_dlt_metadata&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
          Whether to add DLT metadata columns
          (`_dlt_load_id`, `_dlt_id`).
        </PyParameter>

        <PyParameter name="&#x22;add_phlo_metadata&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
          Whether to add Phlo metadata columns
          (`_phlo_ingested_at`, `_phlo_row_id`, `_phlo_partition_date`,
          `_phlo_run_id`).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;pyiceberg.schema.Schema&#x22;">
        Equivalent Iceberg schema with all fields and metadata.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_map_type&#x22;" type="&#x22;(field_name, pandera_type) -> Any&#x22;">
      Map a Pandera-annotated type to an Iceberg type.

      Handles Optional types, generic types, and scalar mappings. Lists and
      dictionaries are explicitly not supported and will raise an error.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        Mapping types::

        str\_type = \_map\_type("name", str)  # Returns StringType()
        opt\_int = \_map\_type("age", Optional\[int])  # Returns LongType()
      </Callout>

      <Callout title="&#x22;Note&#x22;" type="&#x22;note&#x22;">
        Lists and dictionaries are explicitly unsupported and will raise
        `SchemaConversionError`. Complex nested types should be flattened
        or stored as JSON strings.
      </Callout>

      <PySourceCode>
        ```python
        def _map_type(field_name: str, pandera_type: Any) -> Any:
            """Map a Pandera-annotated type to an Iceberg type.

            Handles Optional types, generic types, and scalar mappings. Lists and
            dictionaries are explicitly not supported and will raise an error.

            Args:
                field_name: Source field name for error reporting.
                pandera_type: Annotated Python/Pandera type from the model.

            Returns:
                Corresponding Iceberg type instance.

            Raises:
                SchemaConversionError: If the type is a list, dict, or otherwise
                    cannot be represented in Iceberg.

            Example:
                Mapping types::

                    str_type = _map_type("name", str)  # Returns StringType()
                    opt_int = _map_type("age", Optional[int])  # Returns LongType()

            Note:
                Lists and dictionaries are explicitly unsupported and will raise
                ``SchemaConversionError``. Complex nested types should be flattened
                or stored as JSON strings.

            """
            origin = get_origin(pandera_type)
            if origin is None:
                return _map_scalar(field_name, pandera_type)

            if origin is list:
                raise SchemaConversionError(f"Lists are not supported for field {field_name}")

            if origin is dict:
                raise SchemaConversionError(f"Dicts are not supported for field {field_name}")

            if origin is Any:
                return StringType()

            # Optional[T] / Union[T, None]
            if origin is type(None):
                return StringType()

            args = get_args(pandera_type)
            for arg in args:
                if arg is type(None):
                    continue
                return _map_type(field_name, arg)

            return StringType()
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;field_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Source field name for error reporting.
        </PyParameter>

        <PyParameter name="&#x22;pandera_type&#x22;" type="&#x22;Any&#x22;" value="undefined">
          Annotated Python/Pandera type from the model.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;typing.Any&#x22;">
        Corresponding Iceberg type instance.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_map_scalar&#x22;" type="&#x22;(field_name, t) -> Any&#x22;">
      Map a scalar Python type to an Iceberg type.

      Supports standard Python types and some common extensions like Decimal.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        Scalar mappings::

        assert isinstance(\_map\_scalar("id", int), LongType)
        assert isinstance(\_map\_scalar("name", str), StringType)
        assert isinstance(\_map\_scalar("score", float), DoubleType)
      </Callout>

      <PySourceCode>
        ```python
        def _map_scalar(field_name: str, t: Any) -> Any:
            """Map a scalar Python type to an Iceberg type.

            Supports standard Python types and some common extensions like Decimal.

            Args:
                field_name: Source field name for error reporting.
                t: Scalar Python type (e.g., ``str``, ``int``, ``datetime``).

            Returns:
                Corresponding Iceberg type instance:
                    - ``str`` -> ``StringType()``
                    - ``int`` -> ``LongType()``
                    - ``float`` -> ``DoubleType()``
                    - ``bool`` -> ``BooleanType()``
                    - ``datetime`` -> ``TimestamptzType()``
                    - ``date`` -> ``DateType()``
                    - ``bytes`` -> ``BinaryType()``
                    - ``Decimal`` -> ``DoubleType()``

            Raises:
                SchemaConversionError: If the type is not supported.

            Example:
                Scalar mappings::

                    assert isinstance(_map_scalar("id", int), LongType)
                    assert isinstance(_map_scalar("name", str), StringType)
                    assert isinstance(_map_scalar("score", float), DoubleType)

            """
            if t in (str,):
                return StringType()
            if t in (int,):
                return LongType()
            if t in (float,):
                return DoubleType()
            if t in (bool,):
                return BooleanType()
            if t in (datetime,):
                return TimestamptzType()
            if t in (date,):
                return DateType()
            if t in (bytes,):
                return BinaryType()
            if t in (Decimal,):
                return DoubleType()

            raise SchemaConversionError(f"Unsupported type for field {field_name}: {t}")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;field_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Source field name for error reporting.
        </PyParameter>

        <PyParameter name="&#x22;t&#x22;" type="&#x22;Any&#x22;" value="undefined">
          Scalar Python type (e.g., `str`, `int`, `datetime`).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;typing.Any&#x22;">
        Corresponding Iceberg type instance:

        * `str` -> `StringType()`
        * `int` -> `LongType()`
        * `float` -> `DoubleType()`
        * `bool` -> `BooleanType()`
        * `datetime` -> `TimestamptzType()`
        * `date` -> `DateType()`
        * `bytes` -> `BinaryType()`
        * `Decimal` -> `DoubleType()`
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
