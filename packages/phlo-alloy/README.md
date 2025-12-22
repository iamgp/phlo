# phlo-alloy

Grafana Alloy log collection service plugin for Phlo.

## Description

Grafana Alloy agent for collecting and shipping container logs to Loki.

## Installation

```bash
pip install phlo-alloy
# or
phlo plugin install alloy
```

## Profile

Part of the `observability` profile.

## Usage

```bash
phlo services start --profile observability
# or
phlo services start --service alloy
```

## Dependencies

- loki
