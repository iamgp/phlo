# phlo-polaris

Apache Polaris catalog service plugin for Phlo — an Iceberg REST catalog with
OAuth/RBAC and credential vending, plus snapshot-based Write-Audit-Publish.

## Description

`phlo-polaris` is a **catalog alternative** to `phlo-nessie`, not a Nessie
emulation. It provides the pinned Apache Polaris service with a PostgreSQL
metastore and MinIO/RustFS-compatible S3 storage, and implements Phlo's
snapshot promotion contract: runs stage immutable candidate Iceberg snapshots,
quality checks audit those exact snapshots, and a durable release pointer
(compare-and-swap guarded) exposes them only after promotion.

A project selects one catalog per warehouse: `catalog: nessie` (branch/merge
WAP) or `catalog: polaris` (snapshot WAP). Both may not be the default writer
for the same warehouse. Nessie remains fully supported; use
`phlo polaris migrate-from-nessie` (dry-run by default) to move metadata.

## Installation

```bash
pip install phlo-polaris
# or
phlo plugin install polaris
```

## Configuration

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `POLARIS_PORT` | `10018` | Polaris API host port |
| `POLARIS_ROOT_CREDENTIALS` | `root:s3cr3t` | Bootstrap principal (`client_id:client_secret`), secret |
| `POLARIS_WRITER_CLIENT_ID` | `phlo_writer` | Writer principal client id |
| `POLARIS_WRITER_CLIENT_SECRET` | `phlo-writer-secret` | Writer principal secret, secret |
| `POLARIS_READER_CLIENT_ID` | `phlo_reader` | Reader principal client id |
| `POLARIS_READER_CLIENT_SECRET` | `phlo-reader-secret` | Reader principal secret, secret |

Snapshot WAP additionally requires `wap.strategy: snapshot` in `phlo.yaml`
alongside `wap.enabled: true`.

## Usage

```bash
# Start Polaris and bootstrap the catalog + principals
phlo services start
phlo polaris bootstrap

# Health and registered catalogs
phlo polaris status

# Inventory a Nessie project and register its tables in Polaris (dry run)
phlo polaris migrate-from-nessie
phlo polaris migrate-from-nessie --confirm
```

Trino and PyIceberg authenticate through the REST catalog with the writer
principal and OAuth2; Trino uses Polaris credential vending so no static S3
keys are embedded in query-engine configuration.
