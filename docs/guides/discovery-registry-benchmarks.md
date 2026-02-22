# Discovery And Registry Micro-Benchmarks

This benchmark suite measures the plugin discovery and registry cache hot paths used by the CLI/runtime.

## Coverage

- `service_discovery_cold`: New `ServiceDiscovery` instance, first `discover()` call.
- `service_discovery_warm_cache`: Repeated `discover()` call after cache is loaded.
- `service_discovery_refresh`: Repeated `discover(refresh=True)` calls.
- `registry_fetch_cold`: Cache clear, then first `fetch_registry()` call.
- `registry_fetch_warm_cache`: Repeated cache-hit `fetch_registry()` calls.
- `registry_fetch_refresh`: Repeated `fetch_registry(force_refresh=True)` calls.

## Prerequisites

- Development dependencies installed.

```bash
uv pip install -e .
```

## Run

```bash
uv run python tests/benchmarks/discovery_registry_microbench.py \
  --iterations 300 \
  --warmups 50 \
  --json-output .artifacts/discovery-registry-microbench.json
```

## Expected Output

```text
scenario                            mean_ms     p50_ms     p95_ms     min_ms     max_ms
service_discovery_cold               ...
service_discovery_warm_cache         ...
service_discovery_refresh            ...
registry_fetch_cold                  ...
registry_fetch_warm_cache            ...
registry_fetch_refresh               ...

json_report=.artifacts/discovery-registry-microbench.json
```

## Capture Baseline Numbers For PR Notes

```bash
jq -r '.results[] | [.name, (.mean_ms|tostring), (.p95_ms|tostring)] | @tsv' \
  .artifacts/discovery-registry-microbench.json
```
