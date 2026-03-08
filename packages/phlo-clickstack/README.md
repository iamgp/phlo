# phlo-clickstack

ClickStack observability service for Phlo.

## Overview

`phlo-clickstack` packages the official ClickStack all-in-one image so Phlo can
ship a single OpenTelemetry-native observability target with logs, metrics, and
traces in one UI.

## Installation

```bash
pip install phlo-clickstack
# or
phlo plugin install clickstack
```

## Profile

Part of the `observability` profile.

## Usage

```bash
phlo services start --service clickstack
phlo clickstack query "SELECT count() FROM default.otel_logs"
```

Point `phlo-otel` at ClickStack:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_TRACES_EXPORTER=otlp
export OTEL_METRICS_EXPORTER=otlp
export OTEL_LOGS_EXPORTER=otlp
```
