# PanderaSchemaExtractor (/docs/python-reference/packages/phlo-pandera/phlo_pandera/schema_extractor/PanderaSchemaExtractor)



Extract a NormalizedSchema from a Pandera DataFrameModel subclass.

This class converts Pandera schema definitions into a provider-agnostic
normalized format suitable for storage provider integration and schema
migration tools.

The extractor processes:

* Type annotations (with Optional unwrapping)
* Nullability metadata from Pandera columns
* Field names and ordering

Example:

```python
from pandera.pandas import DataFrameModel, Field

class OrderSchema(DataFrameModel):
    order_id: int = Field(unique=True)
    customer_id: int
    total: float = Field(ge=0)
    notes: str | None = Field(nullable=True)

extractor = PanderaSchemaExtractor()
schema = extractor.extract(OrderSchema)

for field in schema.fields:
    print(f"\{field.name\}: \{field.dtype\} (nullable=\{field.nullable\})")
# Output:
# order_id: int64 (nullable=False)
# customer_id: int64 (nullable=True)
# total: float64 (nullable=True)
# notes: string (nullable=True)
```

Functions [#functions]

<PyFunction name="&#x22;extract&#x22;" type="&#x22;(self, native_schema) -> NormalizedSchema&#x22;">
  Convert a Pandera DataFrameModel class into a NormalizedSchema.

  Processes the class annotations and Pandera column metadata to produce
  a normalized schema with FieldSpec entries for each annotated column.

  <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
    ```python
    from phlo_pandera.schemas import PhloSchema

    class MySchema(PhloSchema):
        id: int
        name: str

    extractor = PanderaSchemaExtractor()
    normalized = extractor.extract(MySchema)
    ```
  </Callout>

  <PySourceCode>
    ````python
    def extract(self, native_schema: type[DataFrameModel]) -> NormalizedSchema:
        """Convert a Pandera DataFrameModel class into a NormalizedSchema.

        Processes the class annotations and Pandera column metadata to produce
        a normalized schema with FieldSpec entries for each annotated column.

        Args:
            native_schema: Pandera DataFrameModel subclass (the class itself,
                not an instance).

        Returns:
            NormalizedSchema with one FieldSpec per annotated column.

        Raises:
            ValueError: If a type cannot be mapped to a canonical dtype.

        Example:
            \```python
            from phlo_pandera.schemas import PhloSchema

            class MySchema(PhloSchema):
                id: int
                name: str

            extractor = PanderaSchemaExtractor()
            normalized = extractor.extract(MySchema)
            \```

        """
        annotations = get_type_hints(native_schema)
        schema_obj = native_schema.to_schema()
        columns = schema_obj.columns

        fields: list[FieldSpec] = []
        for name, annotation in annotations.items():
            if name.startswith("__") or name == "Config":
                continue

            inner_type = _unwrap_optional(annotation)
            dtype = _map_dtype(inner_type)

            nullable = True
            if name in columns:
                nullable = columns[name].nullable

            fields.append(FieldSpec(name=name, dtype=dtype, nullable=nullable))

        return NormalizedSchema(fields=fields)
    ````
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;native_schema&#x22;" type="&#x22;type[DataFrameModel]&#x22;" value="undefined">
      Pandera DataFrameModel subclass (the class itself,
      not an instance).
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo.capabilities.specs.NormalizedSchema&#x22;">
    NormalizedSchema with one FieldSpec per annotated column.
  </PyFunctionReturn>
</PyFunction>
