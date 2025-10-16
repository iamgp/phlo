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

{% macro generate_database_name(custom_database_name, node) -%}
    {%- set catalog_alias = env_var('DUCKLAKE_CATALOG_ALIAS', 'ducklake') -%}
    {{ catalog_alias }}
{%- endmacro %}
