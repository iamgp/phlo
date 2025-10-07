```mermaid
flowchart LR
  subgraph Ingestion
    AB[Airbyte] -->|files/db/api| LZ[(Object Store /raw)]
    AB -->|ref tables| PGS[(Postgres)]
  end

  subgraph Transform & Validate
    GE[Great Expectations]
    DBT[dbt (DuckDB adapter)]
    DGL(DuckLake Catalog in Postgres)
    LZ --> DBT
    DBT --> CUR[(Object Store /curated Parquet)]
    DBT --> DGL
    GE -->|check raw/stg/curated| DBT
  end

  subgraph Serve & BI
    DBT --> PM[Postgres Marts]
    BI[Superset/Metabase]
    BI <---> PM
  end

  DGS[Dagster] ---> AB
  DGS ---> DBT
  DGS ---> GE
  DGS -. schedules/lineage .-> BI

```
