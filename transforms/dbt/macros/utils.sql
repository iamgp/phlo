{% macro batch_partition(expr) -%}
  {{ expr }}
{%- endmacro %}

{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}

{# Removed generate_database_name macro - it causes dbt to validate 'ducklake' catalog
   at compile time before bootstrap macro runs. Instead, rely on 'USE ducklake' command
   in bootstrap macro to set the active database context. #}
