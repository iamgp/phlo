# phlo-clickstack

`phlo-clickstack` is the preferred observability package for Phlo. It packages
the official ClickStack all-in-one image so a single service can receive OTLP
telemetry from `phlo-otel` and provide a unified UI for logs, metrics, and
traces.

## Installation

```bash
pip install phlo-clickstack
```

For the current recommended observability path:

```bash
pip install phlo-otel phlo-metrics phlo-clickstack
```

## Profile

Part of the `observability` profile.

## Ports

| Port | Purpose |
| --- | --- |
| `8080` | ClickStack UI |
| `4317` | OTLP gRPC ingest |
| `4318` | OTLP HTTP ingest |
| `9000` | ClickHouse native port |

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `CLICKSTACK_IMAGE` | `docker.hyperdx.io/hyperdx/hyperdx-all-in-one` | Official ClickStack image |
| `CLICKSTACK_PORT` | `8080` | ClickStack UI port |
| `CLICKSTACK_OTLP_GRPC_PORT` | `4317` | OTLP gRPC ingest port |
| `CLICKSTACK_OTLP_HTTP_PORT` | `4318` | OTLP HTTP ingest port |
| `CLICKSTACK_NATIVE_PORT` | `9000` | ClickHouse native port |
| `CLICKSTACK_PUBLIC_URL` | `""` | Public base URL for observability links |

## Usage

Start ClickStack:

```bash
phlo services start --service clickstack
```

Query the bundled ClickHouse store from a project directory:

```bash
phlo clickstack query "SELECT count() FROM default.otel_logs"
phlo clickstack query --format JSONEachRow "SELECT Timestamp, Body FROM default.otel_logs LIMIT 5"
```

Point `phlo-otel` at ClickStack:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_TRACES_EXPORTER=otlp
export OTEL_METRICS_EXPORTER=otlp
export OTEL_LOGS_EXPORTER=otlp
```

## Positioning

ClickStack is Phlo's premier observability option because it gives one default
destination for:

- traces
- logs
- metrics
- cross-signal navigation

Use Alloy or OpenTelemetry Collector when you need extra routing, fan-out, or
host/container log collection beyond direct OTLP application telemetry.

## Related Packages

- [phlo-otel](phlo-otel.md) - OTLP signal emission
- [phlo-alloy](phlo-alloy.md) - Optional collector and fan-out layer
- [phlo-metrics](phlo-metrics.md) - Neutral observability capability provider
- [Observability Setup](../setup/observability.md) - Stack topology guidance
