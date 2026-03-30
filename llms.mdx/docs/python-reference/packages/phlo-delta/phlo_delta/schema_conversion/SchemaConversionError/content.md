# SchemaConversionError (/docs/python-reference/packages/phlo-delta/phlo_delta/schema_conversion/SchemaConversionError)



Raised when a Pandera schema cannot be converted to a Delta-compatible Arrow schema.

This exception indicates that the source Pandera schema contains unsupported
types, invalid annotations, or other conversion-blocking issues.

Example:
try:
schema = pandera\_to\_delta(InvalidSchema)
except SchemaConversionError as e:
print(f"Conversion failed: \{e}")
