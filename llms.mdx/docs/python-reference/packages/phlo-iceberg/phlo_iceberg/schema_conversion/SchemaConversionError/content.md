# SchemaConversionError (/docs/python-reference/packages/phlo-iceberg/phlo_iceberg/schema_conversion/SchemaConversionError)



Raised when a Pandera schema cannot be converted to an Iceberg schema.

This exception indicates that the schema conversion failed due to:

* Unsupported field types
* Missing type annotations
* Invalid Pandera schema structure
* Type mapping failures

Example:
Handle conversion errors::

from phlo\_iceberg.schema\_conversion import (
pandera\_to\_iceberg, SchemaConversionError
)

try:
schema = pandera\_to\_iceberg(MyComplexModel)
except SchemaConversionError as e:
print(f"Schema conversion failed: \{e}")

Fall back to manual schema definition [#fall-back-to-manual-schema-definition]
