# Tests for Cascade Data Lakehouse Platform

This document outlines the comprehensive test suite required for the Cascade data lakehouse platform. Tests are organized by component/module, covering unit tests, integration tests, end-to-end (e2e) tests, and data quality tests. Each test is described in the format "test that X does this within Y" (where Y indicates the test type or scope).

## Config Module
| Test Description |
|------------------|
| test that config loads environment variables correctly within unit tests |
| test that config validates required fields and raises errors for missing ones within unit tests |
| test that computed fields (e.g., dbt paths, connection strings) are calculated properly within unit tests |
| test that config handles caching and returns the same instance within unit tests |
| test that config generates correct PyIceberg catalog config within unit tests |
| test that config provides valid connection strings for Trino and Postgres within integration tests |

## Iceberg Module
| Test Description |
|------------------|
| test that get_catalog creates and caches catalog instances for different refs within unit tests |
| test that list_tables returns correct tables for namespaces and all namespaces within unit tests |
| test that create_namespace handles existing namespaces without errors within unit tests |
| test that ensure_table creates new tables with correct schema and partitioning within unit tests |
| test that append_to_table adds parquet data to existing tables within unit tests |
| test that get_table_schema retrieves schemas from existing tables within unit tests |
| test that delete_table removes tables correctly within unit tests |
| test that catalog operations work with mock PyIceberg within integration tests |
| test that table operations integrate with Nessie refs within integration tests |

## Ingestion Module (DLT Assets)
| Test Description |
|------------------|
| test that entries asset fetches data from Nightscout API within unit tests (mocked) |
| test that entries asset handles API errors gracefully within unit tests |
| test that entries asset stages data to parquet using DLT within unit tests |
| test that entries asset ensures Iceberg table exists within unit tests |
| test that entries asset appends data to Iceberg table within unit tests |
| test that entries asset returns correct metadata within unit tests |
| test that entries asset integrates with DLT pipeline and Iceberg resources within integration tests |
| test that entries asset processes real partitions without data corruption within integration tests |
| test that ingested data matches expected schema within data quality tests |
| test that ingestion handles empty partitions within e2e tests |
| test that full ingestion pipeline (API → DLT → Iceberg) works end-to-end within e2e tests |

## Transform Module (dbt Assets)
| Test Description |
|------------------|
| test that CustomDbtTranslator assigns correct asset keys within unit tests |
| test that CustomDbtTranslator assigns correct group names within unit tests |
| test that all_dbt_assets runs dbt build command within unit tests (mocked) |
| test that all_dbt_assets runs dbt docs generate within unit tests |
| test that dbt assets handle partitioned runs within unit tests |
| test that dbt assets integrate with DbtCliResource within integration tests |
| test that dbt models transform data correctly from bronze to gold within integration tests |
| test that transformed data maintains referential integrity within data quality tests |
| test that dbt lineage and dependencies are preserved within data quality tests |
| test that full transformation pipeline (raw → bronze → silver → gold) completes within e2e tests |
| test that dbt docs are generated and artifacts copied correctly within e2e tests |

## Publishing Module (Trino to Postgres)
| Test Description |
|------------------|
| test that publish_glucose_marts_to_postgres queries Trino correctly within unit tests (mocked) |
| test that publish_glucose_marts_to_postgres creates Postgres tables within unit tests |
| test that publish_glucose_marts_to_postgres inserts data in batches within unit tests |
| test that publish_glucose_marts_to_postgres handles Postgres connection errors within unit tests |
| test that publishing integrates with Trino and Postgres resources within integration tests |
| test that data transfer preserves row counts and columns within integration tests |
| test that published data matches source Iceberg tables within data quality tests |
| test that Postgres tables are created with correct schemas within data quality tests |
| test that full publishing pipeline (Trino query → Postgres insert) works within e2e tests |

## Quality Module (Asset Checks)
| Test Description |
|------------------|
| test that nightscout_glucose_quality_check queries Trino within unit tests (mocked) |
| test that nightscout_glucose_quality_check validates data with Pandera schema within unit tests |
| test that nightscout_glucose_quality_check handles empty results within unit tests |
| test that nightscout_glucose_quality_check reports failures correctly within unit tests |
| test that quality check integrates with Trino resource within integration tests |
| test that Pandera validation catches schema violations within integration tests |
| test that data conforms to business rules (e.g., glucose ranges) within data quality tests |
| test that quality checks run on partitioned data within data quality tests |
| test that quality checks are triggered after transformations within e2e tests |

## Resources Module
| Test Description |
|------------------|
| test that IcebergResource.get_catalog returns catalog for ref within unit tests |
| test that IcebergResource.ensure_table calls underlying function within unit tests |
| test that IcebergResource.append_parquet calls underlying function within unit tests |
| test that TrinoResource.get_connection creates connections with correct catalog within unit tests |
| test that TrinoResource.cursor context manager works within unit tests |
| test that TrinoResource.query executes and returns results within unit tests |
| test that resources integrate with config for connection parameters within integration tests |
| test that IcebergResource works with actual Nessie within integration tests |
| test that TrinoResource executes real queries within integration tests |
| test that DbtCliResource is configured with correct paths within integration tests |

## Schedules and Sensors Module
| Test Description |
|------------------|
| test that transform_on_new_nightscout_data sensor triggers on asset materialization within unit tests |
| test that sensor skips when no rows loaded within unit tests |
| test that sensor yields correct RunRequest with partition key within unit tests |
| test that daily_ingestion_fallback schedule generates partition keys within unit tests |
| test that schedules and sensors integrate with asset jobs within integration tests |
| test that sensor debouncing prevents excessive triggers within integration tests |
| test that orchestration maintains data lineage within e2e tests |
| test that full pipeline orchestration (ingest → transform → publish) works within e2e tests |

## Definitions Module
| Test Description |
|------------------|
| test that definitions merges all component defs correctly within unit tests |
| test that executor selection works for different platforms within unit tests |
| test that merged definitions include all assets, checks, jobs, schedules, sensors within integration tests |

## Overall System (E2E and Data Quality)
| Test Description |
|------------------|
| test that complete pipeline (ingest → transform → publish) produces consistent data within e2e tests |
| test that data quality is maintained across all layers (raw → bronze → silver → gold → marts) within data quality tests |
| test that system handles branch isolation (Nessie refs) correctly within e2e tests |
| test that time travel queries work on historical data within data quality tests |
| test that schema evolution doesn't break downstream transformations within data quality tests |
| test that concurrent operations (multiple branches) don't cause conflicts within e2e tests |
| test that failure recovery (retries, rollbacks) works within e2e tests |
| test that monitoring and logging capture all pipeline events within e2e tests |
