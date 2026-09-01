# Alerts

A user lists alert destinations, checks alerting status, and can send a test alert. Workspace plugin `alerts` registers `phlo alerts`.

## Sub-features

- `alerts-list` — configured destinations.
- `alerts-status` — system status/statistics.
- `alerts-test` — `test --severity --destination` (sends a test; may hit Slack/email).

## How to get to it (user POV)

- `phlo alerts --help`
- `phlo alerts list`
- `phlo alerts status`
- `phlo alerts test --severity info`

## Driving it with CLI

Preconditions:

- `phlo-alerting` installed. Destinations come from project/env; empty config should still list/status without Docker.

- Help: `uv run --locked phlo alerts --help` → `list`, `status`, `test`.
- List/status: `uv run --locked phlo alerts list` and `phlo alerts status` → exit 0 or a configuration error; capture stdout.
- Do not fire `test` at a real destination in verification unless the dest is a disposable sink.

## Gotchas

- Test is not dry-run; it sends.
- Not Prometheus/`phlo metrics`.
