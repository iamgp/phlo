# phlo-dagster

Dagster orchestration service for Phlo.

## Description

Data orchestration platform for scheduling and monitoring data pipelines. Translates capability specs into Dagster assets, checks, and resources.

## Installation

```bash
pip install phlo-dagster
# or
phlo plugin install dagster
```

## Configuration

| Variable                           | Default     | Description                 |
| ---------------------------------- | ----------- | --------------------------- |
| `DAGSTER_PORT`                     | `3000`      | Dagster webserver port      |
| `PHLO_FORCE_IN_PROCESS_EXECUTOR`   | `false`     | Force in-process executor   |
| `PHLO_FORCE_MULTIPROCESS_EXECUTOR` | `false`     | Force multiprocess executor |
| `WORKFLOWS_PATH`                   | `workflows` | Path to workflow files      |

## Auto-Configuration

This package is **fully auto-configured**:

| Feature                | How It Works                                                              |
| ---------------------- | ------------------------------------------------------------------------- |
| **Adapter Discovery**  | Loads `phlo.plugins.orchestrators` and builds Dagster definitions         |
| **dbt Compilation**    | Auto-compiles dbt on startup via post_start hook                          |
| **Workflow Discovery** | Auto-discovers workflows in `workflows/` directory                        |
| **Metrics Labels**     | Exposes Dagster metrics for Prometheus                                    |

### Post-Start Hook

```yaml
hooks:
  post_start:
    - name: dbt-compile
      command: dbt compile
```

### Capability Discovery

Capability providers are auto-loaded:

- Asset specs from `phlo.plugins.assets`
- Resource specs from `phlo.plugins.resources`
- Check specs from `@phlo_quality`

## Usage

```bash
# Start Dagster
phlo services start --service dagster

# Start with dev mode
phlo services start --dev
```

## Endpoints

- **Web UI**: `http://localhost:3000`
- **GraphQL**: `http://localhost:3000/graphql`
- **Metrics**: `http://localhost:3000/metrics`

## Entry Points

- `phlo.plugins.services` - Provides `DagsterServicePlugin`, `DagsterDaemonServicePlugin`
- `phlo.plugins.orchestrators` - Provides `DagsterOrchestratorAdapter`
- `phlo.plugins.cli` - Provides Dagster CLI commands
