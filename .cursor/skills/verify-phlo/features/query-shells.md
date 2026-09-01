# Query shells

A user runs passthrough CLIs against generated data-plane services. Workspace plugins: `minio`, `postgres`, `trino`, `clickhouse`, `clickstack`. All execute inside or against running containers (**Docker**).

## Sub-features

- `minio` — `phlo minio [MC_ARGS…]` (mc in the MinIO service).
- `postgres` — `phlo postgres [postgres_args]` (`psql` / helpers).
- `trino` — `phlo trino [trino_args]`.
- `clickhouse` — `clickhouse query [SQL] --file --format --timeout`; `clickhouse status`.
- `clickstack` — `clickstack query [SQL] --file --format --timeout`.

## How to get to it (user POV)

- After `phlo services start`:
  - `phlo minio ls local/`
  - `phlo postgres -- psql -c 'SELECT 1'`
  - `phlo trino -- --execute 'SHOW CATALOGS'`
  - `phlo clickhouse query "SELECT 1"`
  - `phlo clickstack query "SELECT 1"`

## Driving it with CLI

Preconditions:

- Matching service running in the isolated compose project. ClickHouse/ClickStack are not default core services; add/profile first.
- Without Docker: commands fail on missing backend/compose; that is the observation.

- Help: `uv run --locked phlo minio --help`, `phlo postgres --help`, `phlo trino --help`, `phlo clickhouse --help`, `phlo clickstack --help` → exit 0 (CLI-only).
- Live query: only if `services start` succeeded. Capture query stdout and exit 0.

**Not live-proven on a Docker-less VM.**

## Gotchas

- These are not `phlo catalog` (Nessie metadata).
- ClickHouse status vs `phlo services status clickhouse` are different commands.
- Timeouts are flags on query (`--timeout` default 30s for clickhouse/clickstack).
