# phlo-pgweb

Pgweb database browser service plugin for Phlo.

## Description

Web-based PostgreSQL database browser.

## Installation

```bash
pip install phlo-pgweb
# or
phlo plugin install pgweb
```

## Configuration

| Variable     | Default | Description |
| ------------ | ------- | ----------- |
| `PGWEB_PORT` | `8082`  | Web UI port |

## Usage

```bash
phlo services start --service pgweb
```

## Dependencies

- postgres

## Endpoints

- **Web UI**: `http://localhost:8082`
