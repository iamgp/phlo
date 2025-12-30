# phlo-alerting

Alert routing and notification plugin for Phlo.

## Overview

`phlo-alerting` routes alerts from quality check failures, telemetry events, and pipeline errors to configured destinations like Slack, PagerDuty, and Email.

## Installation

```bash
pip install phlo-alerting
# or
phlo plugin install alerting
```

## Configuration

| Variable                         | Default | Description                             |
| -------------------------------- | ------- | --------------------------------------- |
| `PHLO_ALERT_SLACK_WEBHOOK`       | -       | Slack incoming webhook URL              |
| `PHLO_ALERT_SLACK_CHANNEL`       | -       | Default Slack channel                   |
| `PHLO_ALERT_PAGERDUTY_KEY`       | -       | PagerDuty Events API v2 key             |
| `PHLO_ALERT_EMAIL_SMTP_HOST`     | -       | SMTP server hostname                    |
| `PHLO_ALERT_EMAIL_SMTP_PORT`     | `587`   | SMTP server port                        |
| `PHLO_ALERT_EMAIL_SMTP_USER`     | -       | SMTP username                           |
| `PHLO_ALERT_EMAIL_SMTP_PASSWORD` | -       | SMTP password                           |
| `PHLO_ALERT_EMAIL_RECIPIENTS`    | `[]`    | Comma-separated list: `a@x.com,b@y.com` |

## Features

### Auto-Configuration

| Feature               | How It Works                                                    |
| --------------------- | --------------------------------------------------------------- |
| **Hook Registration** | Automatically registers as a hook plugin via entry points       |
| **Event Handling**    | Listens for `quality.result` and `telemetry.*` events           |
| **Severity Mapping**  | Maps event severities to alert levels (critical, warning, info) |

### Supported Events

- `quality.result` - Receives quality check results and sends alerts on failures
- `telemetry.*` - Receives telemetry events and forwards to configured destinations

### Severity Levels

| Level      | Description               | Default Destinations |
| ---------- | ------------------------- | -------------------- |
| `critical` | Immediate action required | PagerDuty, Slack     |
| `warning`  | Attention needed          | Slack                |
| `info`     | Informational             | Email (optional)     |

## Usage

### CLI Commands

```bash
# Send a test alert
phlo alerts test --destination slack

# List configured destinations
phlo alerts list

# Silence alerts for a table
phlo alerts silence bronze.problematic_table --duration 1h
```

### Programmatic

```python
from phlo_alerting.manager import AlertManager

manager = AlertManager()
manager.send_alert(
    title="Quality Check Failed",
    message="Null check failed on table users",
    severity="critical",
    metadata={
        "table": "bronze.users",
        "check": "null_check",
        "failed_count": 150
    }
)
```

### Slack Configuration

1. Create a Slack Incoming Webhook
2. Set `PHLO_ALERT_SLACK_WEBHOOK` environment variable
3. Optionally set `PHLO_ALERT_SLACK_CHANNEL`

### PagerDuty Configuration

1. Create a PagerDuty Events API v2 integration
2. Set `PHLO_ALERT_PAGERDUTY_KEY` to the integration key

## Entry Points

| Entry Point          | Plugin                                  |
| -------------------- | --------------------------------------- |
| `phlo.plugins.cli`   | `alerts` CLI command                    |
| `phlo.plugins.hooks` | `AlertingHookPlugin` for event handling |

## Related Packages

- [phlo-quality](phlo-quality.md) - Quality checks
- [phlo-prometheus](phlo-prometheus.md) - Metrics alerting
- [phlo-grafana](phlo-grafana.md) - Alert visualization

## Next Steps

- [Observability Setup](../setup/observability.md) - Complete monitoring
- [Operations Guide](../operations/operations-guide.md) - Alert best practices
