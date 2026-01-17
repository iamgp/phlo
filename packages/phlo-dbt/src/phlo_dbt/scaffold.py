"""Project scaffold helpers for dbt assets."""

from __future__ import annotations


def build_dbt_project(project_name: str) -> str:
    safe_name = project_name.replace("-", "_")
    return f"""name: {safe_name}
version: 1.0.0
config-version: 2

profile: phlo

model-paths: ["models"]
seed-paths: ["seeds"]

# Opt into new SSL behavior to suppress trino-dbt SSL warning
flags:
  require_certificate_validation: true

models:
  {safe_name}:
    +materialized: table
"""


def build_sqlfluff_config() -> str:
    return """[sqlfluff]
dialect = trino
templater = jinja
max_line_length = 120
# Only exclude keywords-as-identifiers rule (requires column renames)
exclude_rules = RF04

[sqlfluff:templater:jinja]
# Ignore undefined jinja variables in dbt
ignore = templating

[sqlfluff:rules]
# Allow trailing commas
allow_trailing_commas = True

[sqlfluff:rules:layout.long_lines]
# Increase line length limit
max_line_length = 120

[sqlfluff:rules:layout.indent]
# Use 4 spaces for indentation
indent_unit = space
tab_space_size = 4

[sqlfluff:rules:capitalisation.keywords]
# SQL keywords should be lowercase
capitalisation_policy = lower

[sqlfluff:rules:aliasing.table]
# Table aliases are required
aliasing = explicit
"""
