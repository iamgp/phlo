# schema_migrator (/docs/python-reference/packages/phlo-iceberg/phlo_iceberg/schema_migrator)



Iceberg implementation of the SchemaMigrator protocol.

This module provides the `IcebergSchemaMigrator` class which implements
Phlo's schema migration capability for Iceberg tables. It supports detecting
schema changes, classifying their impact (safe/warning/breaking), and
applying migrations with approval workflows.

Supported change types:

* `add`: Add new columns (safe if nullable, breaking if required without default)
* `drop`: Remove columns (warning - data loss risk but recoverable via snapshots)
* `rename`: Rename columns (safe in Iceberg via native rename)
* `widen_type`: Type promotion (e.g., int32 -> int64, date -> timestamptz)
* `narrow_type`: Type restriction (breaking - potential data loss)
* `nullability_relaxed`: Make column nullable (safe)
* `nullability_tightened`: Make column required (breaking without default)

Example:
Detect and apply schema migrations::

from phlo\_iceberg.schema\_migrator import IcebergSchemaMigrator
from phlo.capabilities.specs import NormalizedSchema, NormalizedField

Create migrator for specific branch [#create-migrator-for-specific-branch]

migrator = IcebergSchemaMigrator(ref="main")

Define desired schema [#define-desired-schema]

desired = NormalizedSchema(
fields=\[
NormalizedField(name="id", dtype="int64", nullable=False),
NormalizedField(name="name", dtype="string", nullable=True),
NormalizedField(name="score", dtype="float64", nullable=True),
]
)

Detect changes [#detect-changes]

plan = migrator.diff\_schema(table\_name="raw\.users", desired=desired)
print(f"Changes: \{len(plan.changes)}")
print(f"Classification: \{plan.classification}")

Apply if safe or approved [#apply-if-safe-or-approved]

if not plan.requires\_approval:
result = migrator.apply\_plan(plan=plan)
print(f"Applied \{result\['applied\_count']} changes")
else:
print("Breaking changes require approval")

After review: [#after-review]

result = migrator.apply_plan(plan=plan, approved=True) [#result--migratorapply_planplanplan-approvedtrue]

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;IcebergSchemaMigrator&#x22;" href="&#x22;/docs/python-reference/packages/phlo-iceberg/phlo_iceberg/schema_migrator/IcebergSchemaMigrator&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_iceberg_type_to_dtype&#x22;" type="&#x22;(iceberg_type) -> str&#x22;">
      Map a PyIceberg type instance to a canonical dtype string.

      <PySourceCode>
        ```python
        def _iceberg_type_to_dtype(iceberg_type: IcebergType) -> str:
            """Map a PyIceberg type instance to a canonical dtype string."""
            dtype = _ICEBERG_TYPE_MAP.get(type(iceberg_type))
            if dtype is not None:
                return dtype
            return str(iceberg_type)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;iceberg_type&#x22;" type="&#x22;IcebergType&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_dtype_to_iceberg_type&#x22;" type="&#x22;(dtype) -> IcebergType&#x22;">
      Map a canonical dtype string back to a PyIceberg type instance.

      <PySourceCode>
        ```python
        def _dtype_to_iceberg_type(dtype: str) -> IcebergType:
            """Map a canonical dtype string back to a PyIceberg type instance."""
            cls = _DTYPE_TO_ICEBERG.get(dtype)
            if cls is None:
                raise ValueError(f"Unsupported dtype for Iceberg conversion: {dtype}")
            return cls()
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;dtype&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;pyiceberg.types.IcebergType&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
