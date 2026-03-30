# phlo-alloy (/docs/packages/phlo-alloy)



Overview [#overview]

`phlo-alloy` can collect Docker logs and receive OTLP telemetry for forwarding
to downstream observability backends.

Installation [#installation]

```bash
pip install phlo-alloy
# or
phlo plugin install alloy
```

Profile [#profile]

Part of the `observability` profile.

Configuration [#configuration]

| Variable     | Default | Description     |
| ------------ | ------- | --------------- |
| `ALLOY_PORT` | `12345` | Alloy HTTP port |

Features [#features]

Auto-Configuration [#auto-configuration]

| Feature                 | How It Works                                           |
| ----------------------- | ------------------------------------------------------ |
| **Container Discovery** | Auto-discovers all Docker containers via Docker socket |
| **Log Collection**      | Collects stdout/stderr from all containers             |
| **Loki Shipping**       | Ships logs to Loki for storage and querying            |
| **OTLP Receiver**       | Accepts traces, metrics, and logs from `phlo-otel`     |
| **Backend Routing**     | Forwards OTLP signals to one or more downstream sinks  |
| **Metrics Labels**      | Exposes Alloy metrics for Prometheus                   |

Docker Socket Access [#docker-socket-access]

Alloy mounts the Docker socket to discover and collect logs from all containers:

```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:ro
```

Usage [#usage]

Starting the Service [#starting-the-service]

```bash
# Start with observability profile
phlo services start --profile observability

# Or start individually
phlo services start --service alloy
```

OTLP Gateway Pattern [#otlp-gateway-pattern]

Use Alloy when you need a collector in front of the default ClickStack backend
or any multi-backend topology.

Stable OTLP ingress pattern:

```text
phlo-otel -> OTLP -> Alloy -> ClickStack / other downstream backends
```

That lets you:

* keep `phlo-otel` backend-neutral
* route the same telemetry to ClickStack and other downstream backends
* move ClickStack / Tempo / Loki routing changes into Alloy config instead of Python code

Endpoints [#endpoints]

| Endpoint  | URL                              |
| --------- | -------------------------------- |
| **HTTP**  | `http://localhost:12345`         |
| **Ready** | `http://localhost:12345/-/ready` |

Entry Points [#entry-points]

| Entry Point             | Plugin               |
| ----------------------- | -------------------- |
| `phlo.plugins.services` | `AlloyServicePlugin` |

Related Packages [#related-packages]

* [phlo-clickstack](phlo-clickstack.md) - Preferred backend
* [phlo-loki](phlo-loki.md) - Log storage
* [phlo-grafana](phlo-grafana.md) - Log visualization
* [phlo-prometheus](phlo-prometheus.md) - Metrics collection

Next Steps [#next-steps]

* [Observability Setup](../setup/observability.md) - Complete monitoring setup
* [Troubleshooting Guide](../operations/troubleshooting.md) - Debug with logs
