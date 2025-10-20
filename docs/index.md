# Welcome to Cascade

Cascade is a modern data lakehouse platform built on open-source technologies. It provides a complete analytics infrastructure with data ingestion, transformation, querying, and visualization capabilities.

## Features

- **Data Lakehouse Architecture**: Combines the best of data lakes and data warehouses
- **Multi-Engine Analytics**: Support for SQL queries via Trino, DuckDB, and PostgreSQL
- **Data Catalog**: Nessie for Git-like versioning of datasets
- **Orchestration**: Dagster for reliable data pipelines
- **Visualization**: Superset for business intelligence dashboards
- **API Layer**: FastAPI and Hasura GraphQL for programmatic access
- **Observability**: Prometheus, Grafana, and Loki for monitoring and logging

## Quick Start

To get started with Cascade, see the [Quick Start Guide](quick-start.md).

## Architecture

Learn about the system architecture in the [Architecture Overview](architecture.md).

### High-Level Architecture

```mermaid
graph TB
    A[Data Sources] --> B[Ingestion Layer]
    B --> C[Data Lake]
    C --> D[Query Layer]
    D --> E[API Layer]
    E --> F[Visualization]

    subgraph "Ingestion Layer"
        B1[DLT Python]
        B2[PyIceberg]
    end

    subgraph "Data Lake"
        C1[Apache Iceberg]
        C2[Project Nessie]
        C3[MinIO S3]
    end

    subgraph "Query Layer"
        D1[Trino]
        D2[DuckDB]
    end

    subgraph "API Layer"
        E1[FastAPI]
        E2[Hasura GraphQL]
    end

    subgraph "Visualization"
        F1[Superset]
        F2[Grafana]
    end

    B1 --> B2
    C1 --> C2
    C2 --> C3
    D1 --> C1
    D2 --> C1
    E1 --> D1
    E2 --> D1
    F1 --> E1
    F2 --> D1

    style A fill:#e1f5fe
    style F fill:#f3e5f5
```

## Configuration

Configure your Cascade environment using the [Configuration Guide](configuration.md).
