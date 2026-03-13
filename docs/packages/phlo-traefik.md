# phlo-traefik

`phlo-traefik` provides a local reverse proxy for accessing Phlo services by
hostname instead of port number.

## Installation

```bash
pip install phlo-traefik
```

## Profile

Part of the `proxy` profile.

## Ports

| Port | Purpose |
| --- | --- |
| `80` | HTTP entrypoint (configurable via `TRAEFIK_HTTP_PORT`) |

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `TRAEFIK_HTTP_PORT` | `80` | Host port for Traefik HTTP entrypoint |
| `TRAEFIK_DOMAIN` | `phlo.localhost` | Base domain for service hostnames |

## Usage

Start Traefik:

```bash
phlo services start --service traefik
```

Or start with the proxy profile:

```bash
phlo services start --profile proxy
```

## Routed Services

When Traefik is enabled, services are accessible at friendly hostnames:

| Hostname | Service | Port |
| --- | --- | --- |
| `dagster.phlo.localhost` | Dagster | 3000 |
| `minio.phlo.localhost` | MinIO Console | 9001 |
| `minio-api.phlo.localhost` | MinIO API | 9000 |
| `trino.phlo.localhost` | Trino | 8080 |
| `nessie.phlo.localhost` | Nessie | 19120 |
| `clickhouse.phlo.localhost` | ClickHouse | 8123 |
| `api.phlo.localhost` | Phlo API | 4000 |
| `traefik.phlo.localhost` | Traefik Dashboard | (internal) |

## Accessing Services

```bash
# Open Dagster in browser
open http://dagster.phlo.localhost

# Query Trino
curl http://trino.phlo.localhost/v1/info

# Access MinIO Console
open http://minio.phlo.localhost

# Access Traefik dashboard
open http://traefik.phlo.localhost
```

## Troubleshooting

### Port 80 already in use

If port 80 is already in use on your machine, set a custom port in
`.phlo/.env.local`:

```bash
TRAEFIK_HTTP_PORT=8088
```

Then access services with the port: `http://dagster.phlo.localhost:8088`

### Service returns 404

Check that:

1. Traefik is running: `docker ps | grep traefik`
2. The service has `traefik.enable: "true"` in its labels
3. The `Host()` rule matches the hostname you're using
