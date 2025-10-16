{% macro ducklake__bootstrap() %}
  {# DuckLake bootstrap macro executed on dbt run start #}
  {% set catalog_alias = env_var('DUCKLAKE_CATALOG_ALIAS', 'ducklake') %}
  {% set catalog_db = env_var('DUCKLAKE_CATALOG_DATABASE', 'ducklake_catalog') %}
  {% set data_path = env_var('DUCKLAKE_DATA_PATH', 's3://lake/ducklake') %}
  {% set default_dataset = env_var('DUCKLAKE_DEFAULT_DATASET', 'raw') %}
  {% set staging_dataset = default_dataset ~ '_staging' %}

  {% set minio_host = env_var('MINIO_HOST', 'minio') %}
  {% set minio_port = env_var('MINIO_API_PORT', '9000') %}
  {% set minio_endpoint = minio_host ~ ':' ~ minio_port %}
  {% set minio_user = env_var('MINIO_ROOT_USER') %}
  {% set minio_password = env_var('MINIO_ROOT_PASSWORD') %}
  {% set minio_region = env_var('DUCKLAKE_REGION', 'eu-west-1') %}
  {% set use_ssl = env_var('DUCKLAKE_USE_SSL', 'false') | lower %}

  {% set postgres_host = env_var('POSTGRES_HOST', 'postgres') %}
  {% set postgres_port = env_var('POSTGRES_PORT', '5432') %}
  {% set postgres_user = env_var('POSTGRES_USER') %}
  {% set postgres_password = env_var('POSTGRES_PASSWORD') %}

  {% set retry_count = env_var('DUCKLAKE_MAX_RETRY', '100') %}
  {% set retry_wait = env_var('DUCKLAKE_RETRY_WAIT_MS', '200') %}
  {% set retry_backoff = env_var('DUCKLAKE_RETRY_BACKOFF', '1.8') %}

  {% set pg_secret = catalog_alias ~ '_postgres_secret' %}
  {% set s3_secret = catalog_alias ~ '_s3_secret' %}
  {% set ducklake_secret = catalog_alias ~ '_ducklake_secret' %}
  {% set ssl_flag = 'TRUE' if use_ssl == 'true' else 'FALSE' %}
  {% set s3_ssl_flag = 'true' if use_ssl == 'true' else 'false' %}

  {# Install and configure extensions/settings #}
  {% set statements = [
    "INSTALL ducklake",
    "LOAD ducklake",
    "INSTALL httpfs",
    "LOAD httpfs",
    "INSTALL postgres",
    "LOAD postgres",
    "SET s3_endpoint='" ~ minio_endpoint ~ "'",
    "SET s3_url_style='path'",
    "SET s3_use_ssl=" ~ s3_ssl_flag,
    "SET s3_access_key_id='" ~ minio_user ~ "'",
    "SET s3_secret_access_key='" ~ minio_password ~ "'",
    "SET s3_region='" ~ minio_region ~ "'",
    "SET ducklake_max_retry_count=" ~ retry_count,
    "SET ducklake_retry_wait_ms=" ~ retry_wait,
    "SET ducklake_retry_backoff=" ~ retry_backoff
  ] %}

  {% for stmt in statements %}
    {% do run_query(stmt) %}
  {% endfor %}

  {% set create_pg_secret %}
    CREATE OR REPLACE SECRET {{ pg_secret }} (
      TYPE postgres,
      HOST '{{ postgres_host }}',
      PORT '{{ postgres_port }}',
      DATABASE '{{ catalog_db }}',
      USER '{{ postgres_user }}',
      PASSWORD '{{ postgres_password }}'
    )
  {% endset %}
  {% do run_query(create_pg_secret) %}

  {% set create_s3_secret %}
    CREATE OR REPLACE SECRET {{ s3_secret }} (
      TYPE s3,
      PROVIDER config,
      KEY_ID '{{ minio_user }}',
      SECRET '{{ minio_password }}',
      REGION '{{ minio_region }}',
      ENDPOINT '{{ minio_endpoint }}',
      URL_STYLE 'path',
      USE_SSL {{ ssl_flag }}
    )
  {% endset %}
  {% do run_query(create_s3_secret) %}

  {% set create_ducklake_secret %}
    CREATE OR REPLACE SECRET {{ ducklake_secret }} (
      TYPE ducklake,
      METADATA_PATH '',
      DATA_PATH '{{ data_path }}',
      METADATA_PARAMETERS MAP {'TYPE': 'postgres','SECRET': '{{ pg_secret }}'}
    )
  {% endset %}
  {% do run_query(create_ducklake_secret) %}

  {% set dbs = run_query("PRAGMA database_list") %}
  {% set aliases = [] %}
  {% if dbs is not none %}
    {% for row in dbs %}
      {% do aliases.append(row['name']) %}
    {% endfor %}
  {% endif %}

  {% if catalog_alias not in aliases %}
    {% set attach_sql = "ATTACH 'ducklake:" ~ ducklake_secret ~ "' AS " ~ catalog_alias %}
    {% do run_query(attach_sql) %}
  {% endif %}

  {% do run_query("USE " ~ catalog_alias) %}

  {% set schemas = [
    default_dataset,
    staging_dataset,
    "main_" ~ default_dataset,
    "main_staging",
    "main_intermediate",
    "main_curated",
    "main_marts"
  ] %}

  {% for schema in schemas %}
    {% do run_query('CREATE SCHEMA IF NOT EXISTS "' ~ schema ~ '"') %}
  {% endfor %}

  {% do run_query("SET search_path = '" ~ default_dataset ~ "'") %}
{% endmacro %}
