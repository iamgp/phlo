# PhloSchema (/docs/python-reference/packages/phlo-pandera/phlo_pandera/schemas/base/PhloSchema)



Base schema with phlo smart defaults.

Extends Pandera DataFrameModel with standard phlo configuration:

* `strict=False`: Allow extra columns (DLT metadata like `_dlt_id`, `_dlt_load_id`)
* `coerce=True`: Automatically coerce types to match schema

This eliminates the need to define Config on every schema subclass.
