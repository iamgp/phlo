# Service Packages

Phlo services are distributed as Python packages. Each service package ships its own `service.yaml`
definition and registers a `phlo.plugins.services` entry point so the CLI can discover it.

## Why packages?

- One service per package, so services can be installed or swapped independently.
- Services use the same plugin discovery flow as sources/quality/transforms.
- Core services are versioned alongside Phlo, while optional services can be added on demand.

## Core service packages

Install the core services alongside the CLI:

```bash
uv pip install -e ".[core-services]"
```

Core service packages:

- `phlo-postgres`
- `phlo-minio`
- `phlo-nessie`
- `phlo-trino`
- `phlo-dagster`

## Optional service packages

Optional services are installed independently. Use the plugin installer or `pip`/`uv` directly:

```bash
phlo plugin install phlo-observatory
uv pip install phlo-pgweb
```

Optional packages include:

- `phlo-observatory`
- `phlo-pgweb`
- `phlo-superset`
- `phlo-postgrest`
- `phlo-hasura`
- `phlo-fastapi`
- `phlo-prometheus`
- `phlo-grafana`
- `phlo-loki`
- `phlo-alloy`

## Discovering installed services

List installed service plugins:

```bash
phlo plugin list --type services
```

List registry services (installed + available):

```bash
phlo plugin list --type services --all
```

## Development mode

In dev mode, the CLI mounts local package sources into containers. Use `--phlo-source` to point to
the monorepo root:

```bash
phlo services init --dev --phlo-source /path/to/phlo
phlo services start --dev --phlo-source /path/to/phlo
```

Dev mode relies on each service package defining a `dev` override in its `service.yaml` for command,
volumes, and environment.
