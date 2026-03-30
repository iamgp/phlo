# checks_extra (/docs/python-reference/packages/phlo-pandera/phlo_pandera/checks_extra)



Extended quality check classes: SchemaCheck, CustomSQLCheck, PatternCheck.

This module provides additional quality check types that extend the core checks
from `checks.py`. These checks support more advanced validation scenarios
including schema validation, custom SQL assertions, and pattern matching.

These checks are split into a separate module to keep individual files under
500 lines as per project conventions, while maintaining a clean organization
of related functionality.

Available Extended Checks:

* **SchemaCheck**: Validates DataFrame against a Pandera DataFrameModel schema,
  including type checking, constraint validation, and nullability checks.
* **CustomSQLCheck**: Executes arbitrary SQL queries against the data using
  DuckDB, enabling complex business rule validation.
* **PatternCheck**: Validates that string column values match regular
  expression patterns, useful for format validation (emails, postal codes, etc.).

Example Usage:

```python
from phlo_pandera import SchemaCheck, CustomSQLCheck, PatternCheck, phlo_pandera
from my_schemas import CustomerSchema

@phlo_pandera(
    table="bronze.customers",
    checks=[
        # Validate against Pandera schema
        SchemaCheck(schema=CustomerSchema),
        # Custom SQL validation
        CustomSQLCheck(
            name_="valid_email",
            sql="SELECT email LIKE '%@%.%' FROM data",
        ),
        # Pattern matching for postal codes
        PatternCheck(
            column="postal_code",
            pattern=r"^\d\{5\}(-\d\{4\})?$",
        ),
    ],
)
def customer_quality():
    pass
```

See Also:

* `checks.py`: Core quality check implementations
* `reconciliation.py`: Cross-table reconciliation checks
* `decorator.py`: `@phlo_pandera` decorator for integration

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;SchemaCheck&#x22;" href="&#x22;/docs/python-reference/packages/phlo-pandera/phlo_pandera/checks_extra/SchemaCheck&#x22;" />

      <Card title="&#x22;CustomSQLCheck&#x22;" href="&#x22;/docs/python-reference/packages/phlo-pandera/phlo_pandera/checks_extra/CustomSQLCheck&#x22;" />

      <Card title="&#x22;PatternCheck&#x22;" href="&#x22;/docs/python-reference/packages/phlo-pandera/phlo_pandera/checks_extra/PatternCheck&#x22;" />
    </Cards>
  </Tab>
</Tabs>
