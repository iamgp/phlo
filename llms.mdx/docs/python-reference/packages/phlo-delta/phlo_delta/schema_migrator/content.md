# schema_migrator (/docs/python-reference/packages/phlo-delta/phlo_delta/schema_migrator)



Delta Lake implementation of the SchemaMigrator protocol.

This module provides schema migration capabilities for Delta Lake tables,
including schema diffing, migration planning, and schema change application.
It supports add, drop, rename, type widening/narrowing, and nullability changes.

Example:
from phlo\_delta.schema\_migrator import DeltaSchemaMigrator
from phlo.capabilities.specs import NormalizedSchema

migrator = DeltaSchemaMigrator()
plan = migrator.diff\_schema(table\_name="raw\.events", desired=normalized\_schema)
result = migrator.apply\_plan(plan=plan, approved=True)

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;DeltaSchemaMigrator&#x22;" href="&#x22;/docs/python-reference/packages/phlo-delta/phlo_delta/schema_migrator/DeltaSchemaMigrator&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_arrow_type_to_dtype&#x22;" type="&#x22;(arrow_type) -> str&#x22;">
      Map a PyArrow type instance to a canonical dtype string.

      Converts PyArrow data types to string representations used in
      schema migration operations.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        dtype = \_arrow\_type\_to\_dtype(pa.int64())

        Returns: "int64" [#returns-int64]
      </Callout>

      <PySourceCode>
        ```python
        def _arrow_type_to_dtype(arrow_type: pa.DataType) -> str:
            """Map a PyArrow type instance to a canonical dtype string.

            Converts PyArrow data types to string representations used in
            schema migration operations.

            Args:
                arrow_type: PyArrow data type instance.

            Returns:
                str: Canonical dtype string (e.g., "string", "int64", "timestamptz").

            Example:
                dtype = _arrow_type_to_dtype(pa.int64())
                # Returns: "int64"

            """
            dtype = _ARROW_TYPE_MAP.get(arrow_type)
            if dtype is not None:
                return dtype
            if isinstance(arrow_type, pa.TimestampType):
                if arrow_type.tz:
                    return "timestamptz"
                return "timestamp"
            return str(arrow_type)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;arrow_type&#x22;" type="&#x22;pa.DataType&#x22;" value="undefined">
          PyArrow data type instance.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Canonical dtype string (e.g., "string", "int64", "timestamptz").
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_dtype_to_arrow_type&#x22;" type="&#x22;(dtype) -> pa.DataType&#x22;">
      Map a canonical dtype string back to a PyArrow type.

      Converts string dtype representations to PyArrow data types for
      schema construction.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        arrow\_type = \_dtype\_to\_arrow\_type("int64")

        Returns: pa.int64() [#returns-paint64]
      </Callout>

      <PySourceCode>
        ```python
        def _dtype_to_arrow_type(dtype: str) -> pa.DataType:
            """Map a canonical dtype string back to a PyArrow type.

            Converts string dtype representations to PyArrow data types for
            schema construction.

            Args:
                dtype: Canonical dtype string.

            Returns:
                pa.DataType: Corresponding PyArrow data type.

            Raises:
                ValueError: If the dtype string is not supported.

            Example:
                arrow_type = _dtype_to_arrow_type("int64")
                # Returns: pa.int64()

            """
            result = _DTYPE_TO_ARROW.get(dtype)
            if result is None:
                raise ValueError(f"Unsupported dtype for Delta conversion: {dtype}")
            return result
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;dtype&#x22;" type="&#x22;str&#x22;" value="undefined">
          Canonical dtype string.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;pyarrow.DataType&#x22;">
        pa.DataType: Corresponding PyArrow data type.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
