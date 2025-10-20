Awesome — here’s both deliverables:

---

# Iceberg + Nessie Architecture (OSS-first, enterprise-ready)

## What you’ll run

- **MinIO (S3-compatible object store)** — holds Parquet data + Iceberg metadata files. ([MinIO Blog][1])
- **Project Nessie (Git-like catalog)** — branches/tags, cross-table transactions, point-in-time views. ([projectnessie.org][2])
- **Query/compute engine** — **Trino** (recommended) or Spark; both have 1st-class Iceberg connectors. ([Trino][3])
- **dbt** — use **dbt-trino** _or_ **dbt-spark** with Iceberg. (dbt also announced Iceberg tables support on BigQuery if that path appeals later.) ([Medium][4])
- **Dagster** — orchestration for dbt + Python assets. ([docs.dagster.io][5])
- **(Optional) DuckDB** — fast ad-hoc reads of Iceberg via the DuckDB **iceberg** extension. ([DuckDB][6])

## Logical layout (high level)

```mermaid
flowchart LR
  subgraph Sources
    NS[Nightscout API]
    CSV[CSV/Excel Drops]
  end

  subgraph Ingestion
    DLT[DLT (Python)]
    PYI[PyIceberg (register/append)]
  end

  subgraph Lake[Lakehouse on MinIO]
    ICE[Apache Iceberg Tables]
    META[Nessie Catalog]
  end

  subgraph Compute
    TR[Trino]
    SP[Spark]:::opt
    DDB[(DuckDB - iceberg ext)]:::opt
  end

  subgraph Transform
    DBT[dbt (Trino/Spark)]
  end

  subgraph BI
    PG[(Postgres marts)]:::opt
    SS[Superset]
  end

  NS --> DLT --> PYI --> ICE
  CSV --> DLT
  META <---> ICE
  TR <--> ICE
  SP <--> ICE
  DDB --> ICE
  DBT --> TR
  DBT --> SP
  TR --> SS
  PG --> SS
classDef opt fill:#eee,stroke:#bbb,color:#333;
```

**Why this works**

- **Iceberg** is the open table format providing **ACID, schema evolution, partitioning, and time-travel**. ([Amazon Web Services, Inc.][7])
- **Nessie** gives **branching, tagging, and cross-table commits** (e.g., build on a feature branch; fast “publish” via merge). ([projectnessie.org][2])
- **dbt** targets Iceberg through **Trino** or **Spark** adapters — no compile-time bootstrap hacks. ([Trino][3])
- **MinIO** is a proven S3 backend for Iceberg. ([MinIO Blog][1])
- **DuckDB** can still query Iceberg tables locally for rapid interactive analysis. ([DuckDB][6])

---

# POC Plan (2–3 days of focused work)

## 0) Outcomes you’ll prove

1. End-to-end load from Nightscout → **Iceberg** on MinIO (append daily partitions).
2. **dbt** builds/updates **Iceberg** models via **Trino** (or Spark).
3. **Nessie** branch workflow (dev → main) + time-travel query.
4. Optional: publish curated **marts** to Postgres for Superset concurrency.

---

## 1) Stand up the core services

- **MinIO**: 1–3 node dev cluster; create a bucket `lake/`. ([MinIO Blog][1])
- **Nessie**: run the server (Docker/K8s); note the REST endpoint and create branches `main`, `dev`. ([projectnessie.org][2])
- **Trino**: enable **Iceberg connector**, pointing at MinIO (S3) and Nessie catalog (Iceberg REST). Validate with `SHOW CATALOGS;` and `CREATE SCHEMA ...`. ([Trino][3])

---

## 2) Ingestion (DLT → Iceberg)

Two simple routes — pick one:

- **Route A (recommended)**: Land raw JSON → Parquet in `s3://lake/stage/nightscout/…`; then **CTAS** into Iceberg with Trino:
  `CREATE TABLE iceberg.raw.entries AS SELECT * FROM parquet_scan('s3://lake/stage/...');` ([Trino][3])

- **Route B (Python-native)**: Use **PyIceberg** to create/append directly to Iceberg tables from your DLT asset (works nicely in Dagster). ([PyIceberg][8])

Either way you’re avoiding the DuckLake bootstrap problem and writing **directly to Iceberg tables**.

---

## 3) dbt on Iceberg (via Trino)

- Use **dbt-trino**; configure a target catalog `iceberg` that points to your Trino Iceberg connector. (dbt-spark is equally valid if you prefer Spark.) ([Medium][4])
- Create **bronze → silver → gold** models with `materialized: table` (Iceberg tables by default).
- Run `dbt build` against the **Nessie `dev` branch** (set via Trino Iceberg/Nessie catalog config).
- After checks, **merge `dev` → `main`** in Nessie to “publish” the whole catalog atomically. ([projectnessie.org][9])

---

## 4) Orchestration (Dagster)

- Model raw tables (DLT) and dbt models as **software-defined assets**; wire daily partitions. ([docs.dagster.io][5])
- Sequence: `ingest_raw → bronze → silver → gold → (optional) publish marts to Postgres → Superset`.

---

## 5) Optional marts & BI

- Keep **Postgres marts** for high-concurrency dashboards; materialize from Trino with dbt or simple `COPY`/CTAS.
- Point **Superset** at both **Trino** (for lake queries) and **Postgres** (for hot marts).

---

## 6) Nice POC demos to capture

- **Time travel**: query yesterday’s snapshot vs. today’s. ([Estuary][10])
- **Branching**: run dbt on `dev`, validate in Superset, then **Nessie merge** to publish. ([projectnessie.org][9])
- **DuckDB**: local `INSTALL iceberg; LOAD iceberg; SELECT * FROM iceberg_scan('s3://...');` for fast ad-hoc reads. ([DuckDB][6])

---

## Example snippets (trim to taste)

**Trino Iceberg connector (catalog properties)**

```properties
connector.name=iceberg
iceberg.catalog.type=rest
iceberg.rest-catalog.uri=http://nessie:19120/api/v1
iceberg.rest-catalog.warehouse=s3://lake/warehouse
fs.native-s3.enabled=true
s3.endpoint=http://minio:9000
s3.path-style-access=true
s3.aws-access-key=<MINIO_KEY>
s3.aws-secret-key=<MINIO_SECRET>
```

(Adjust for your network; the key bit is **Iceberg REST to Nessie** + **S3 to MinIO**.) ([Trino][3])

**dbt `profiles.yml` (trino target)**

```yaml
iceberg_trino:
  target: dev
  outputs:
    dev:
      type: trino
      host: trino
      port: 8080
      user: dbt
      catalog: iceberg # the Trino catalog above
      schema: bronze # dbt will create schemas as Iceberg namespaces
      threads: 8
```

(db t with Trino + Iceberg is a common pattern.) ([Medium][4])

**Create initial raw table via Trino CTAS**

```sql
CREATE SCHEMA IF NOT EXISTS iceberg.raw WITH (location='s3://lake/warehouse/raw/');
CREATE TABLE IF NOT EXISTS iceberg.raw.entries AS
SELECT * FROM parquet_metadata('$s3_path_to_staged_parquet') WITH NO DATA;
-- then INSERT INTO ... from the staged files or DLT job
```

([Trino][3])

**PyIceberg quickstart idea (from a Dagster asset)**

```python
from pyiceberg.catalog import load_catalog
cat = load_catalog("rest", **{"uri":"http://nessie:19120/api/v1", "warehouse":"s3://lake/warehouse"})
if "raw.entries" not in cat.list_tables("raw"):
    cat.create_table("raw.entries", schema=..., partition_spec=...)
table = cat.load_table("raw.entries")
table.append(your_arrow_or_pandas_df)
```

([PyIceberg][8])

---

## Migration tips from DuckLake

- Keep your existing **DLT** jobs; change the sink to **stage to S3 (MinIO)** + register into **Iceberg** (Trino CTAS or PyIceberg).
- Replace **dbt-duckdb** with **dbt-trino** (or dbt-spark). No compile-time bootstrap hacks required. ([Medium][4])
- Preserve your bronze/silver/gold structure 1:1 in Iceberg namespaces.
- For ad-hoc analysis, use **DuckDB’s iceberg extension** instead of DuckLake. ([DuckDB][6])

---

## Why this beats DuckLake for you

- **Standardized table format & catalog** (Iceberg + Nessie) with **ACID, time travel, branching**. ([Estuary][10])
- **dbt works out of the box** with Trino/Spark adapters. ([Medium][4])
- **Broad engine choice** now and enterprise on-ramps later (e.g., Tabular, Dremio, Snowflake Iceberg). ([Snowflake][11])

---

If you want, I can turn this into:

- a **decision table** for management (costs, OPEX/CAPEX, risks), and
- a **Dagster + dbt starter repo layout** with sample assets, profiles, and CI checks.

[1]: https://blog.min.io/a-developers-introduction-to-apache-iceberg-using-minio/?utm_source=chatgpt.com "A Developer's Introduction to Apache Iceberg using MinIO"
[2]: https://projectnessie.org/?utm_source=chatgpt.com "Project Nessie: Transactional Catalog for Data Lakes with Git ..."
[3]: https://trino.io/docs/current/connector/iceberg.html?utm_source=chatgpt.com "Iceberg connector — Trino 477 Documentation"
[4]: https://medium.com/tech-with-abhishek/integrating-dbt-with-apache-iceberg-and-open-lakehouse-architectures-da244aa26a5d?utm_source=chatgpt.com "Integrating dbt with Apache Iceberg and Open Lakehouse ..."
[5]: https://docs.dagster.io/api/libraries/dagster-dbt?utm_source=chatgpt.com "dbt (dagster-dbt)"
[6]: https://duckdb.org/docs/stable/core_extensions/iceberg/overview.html?utm_source=chatgpt.com "Iceberg Extension"
[7]: https://aws.amazon.com/what-is/apache-iceberg/?utm_source=chatgpt.com "What is Apache Iceberg? - Iceberg Tables Explained"
[8]: https://py.iceberg.apache.org/?utm_source=chatgpt.com "PyIceberg"
[9]: https://projectnessie.org/guides/?utm_source=chatgpt.com "Transactional Catalog for Data Lakes with Git-like semantics"
[10]: https://estuary.dev/blog/time-travel-apache-iceberg/?utm_source=chatgpt.com "Apache Iceberg Time Travel Guide: Snapshots, Queries & ..."
[11]: https://www.snowflake.com/en/fundamentals/apache-iceberg-tables/?utm_source=chatgpt.com "What Are Apache Iceberg Tables?"
