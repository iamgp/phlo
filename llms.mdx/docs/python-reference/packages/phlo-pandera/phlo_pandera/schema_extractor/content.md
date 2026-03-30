# schema_extractor (/docs/python-reference/packages/phlo-pandera/phlo_pandera/schema_extractor)



Pandera SchemaExtractor implementation.

This module provides the PanderaSchemaExtractor class which converts Pandera
DataFrameModel subclasses into provider-agnostic NormalizedSchema objects.
These normalized schemas can be used by storage providers (Iceberg, Delta, etc.)
and schema migration tooling.

The extractor handles:

* Python type to storage type mapping
* Optional type unwrapping (Optional\[T] -> T)
* Nullability detection from Pandera schema metadata
* Support for common Python types used in data engineering

Type Mapping:
The extractor maps Python types to canonical storage types:

* str -> "string"
* int -> "int64"
* float -> "float64"
* bool -> "bool"
* datetime -> "timestamptz"
* date -> "date"
* bytes -> "binary"
* Decimal -> "float64"

Example:

```python
from pandera.pandas import DataFrameModel, Field
from phlo_pandera.schema_extractor import PanderaSchemaExtractor

class CustomerSchema(DataFrameModel):
    customer_id: int = Field(gt=0)
    email: str | None = Field(nullable=True)
    created_at: datetime

extractor = PanderaSchemaExtractor()
normalized = extractor.extract(CustomerSchema)

# normalized.fields contains:
# - FieldSpec(name="customer_id", dtype="int64", nullable=False)
# - FieldSpec(name="email", dtype="string", nullable=True)
# - FieldSpec(name="created_at", dtype="timestamptz", nullable=True)
```

See Also:

* `schemas/base.py`: PhloSchema base class
* `schemas/asset_outputs.py`: Output schema definitions

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;PanderaSchemaExtractor&#x22;" href="&#x22;/docs/python-reference/packages/phlo-pandera/phlo_pandera/schema_extractor/PanderaSchemaExtractor&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_map_dtype&#x22;" type="&#x22;(python_type) -> str&#x22;">
      Map a scalar Python type to a canonical dtype string.

      Converts Python type annotations to canonical storage type strings
      recognized by storage providers like Iceberg and Delta Lake.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        _map_dtype(str)    # Returns: "string"
        _map_dtype(int)    # Returns: "int64"
        _map_dtype(float)  # Returns: "float64"
        ```
      </Callout>

      <PySourceCode>
        ````python
        def _map_dtype(python_type: type) -> str:
            """Map a scalar Python type to a canonical dtype string.

            Converts Python type annotations to canonical storage type strings
            recognized by storage providers like Iceberg and Delta Lake.

            Args:
                python_type: Scalar Python type annotation.

            Returns:
                Canonical dtype string recognized by storage providers.

            Raises:
                ValueError: If the type has no known mapping.

            Example:
                \```python
                _map_dtype(str)    # Returns: "string"
                _map_dtype(int)    # Returns: "int64"
                _map_dtype(float)  # Returns: "float64"
                \```

            """
            dtype = _DTYPE_MAP.get(python_type)
            if dtype is None:
                raise ValueError(f"Unsupported type: {python_type}")
            return dtype
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;python_type&#x22;" type="&#x22;type&#x22;" value="undefined">
          Scalar Python type annotation.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Canonical dtype string recognized by storage providers.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_unwrap_optional&#x22;" type="&#x22;(tp) -> type&#x22;">
      Unwrap Optional\[T] / Union\[T, None] to the inner type T.

      Strips the Optional wrapper from type annotations to get the underlying
      type for dtype mapping. Returns the type unchanged when it is not
      an optional wrapper.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        _unwrap_optional(Optional[str])  # Returns: str
        _unwrap_optional(str | None)   # Returns: str
        _unwrap_optional(int)          # Returns: int
        ```
      </Callout>

      <PySourceCode>
        ````python
        def _unwrap_optional(tp: Any) -> type:
            """Unwrap Optional[T] / Union[T, None] to the inner type T.

            Strips the Optional wrapper from type annotations to get the underlying
            type for dtype mapping. Returns the type unchanged when it is not
            an optional wrapper.

            Args:
                tp: Type annotation that may be wrapped in Optional.

            Returns:
                The inner type if Optional, otherwise the type unchanged.

            Example:
                \```python
                _unwrap_optional(Optional[str])  # Returns: str
                _unwrap_optional(str | None)   # Returns: str
                _unwrap_optional(int)          # Returns: int
                \```

            """
            origin = get_origin(tp)
            if origin is Union or isinstance(tp, types.UnionType):
                args = [a for a in get_args(tp) if a is not type(None)]
                if len(args) == 1:
                    return args[0]
            return tp
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;tp&#x22;" type="&#x22;Any&#x22;" value="undefined">
          Type annotation that may be wrapped in Optional.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;type&#x22;">
        The inner type if Optional, otherwise the type unchanged.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
