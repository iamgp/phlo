# Sling

A user lists Sling connections, discovers streams, and runs replications. Workspace plugin `sling` registers `phlo sling`.

## Sub-features

- `sling-conns` — `sling conns --auto`
- `sling-discover` — `sling discover CONNECTION --schema --format`
- `sling-run` — `sling run --replication/-r --source/-s --target/-t --stream --object --mode` (mutation)

## How to get to it (user POV)

- `phlo init … --template sling-replication` then `phlo sling conns`
- `phlo sling discover <connection>`
- `phlo sling run -r path/to/replication.yaml`

## Driving it with CLI

Preconditions:

- `phlo-sling` installed. Connections often need env from generated services (**Docker**).
- Run is authorization-gated.

- Help: `uv run --locked phlo sling --help` → `conns`, `discover`, `run`.
- `conns` without binaries/env: capture Sling CLI failure; do not invent connection names.

## Gotchas

- Ingestion authoring for Sling is `phlo.ingest.sling` ([python-authoring.md](python-authoring.md)), not this CLI group alone.
- Template `sling-replication` requires package `phlo-sling`.
