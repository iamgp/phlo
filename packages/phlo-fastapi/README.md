# phlo-fastapi

FastAPI backend service plugin for Phlo.

## Description

FastAPI-based backend service for custom API endpoints.

## Installation

```bash
pip install phlo-fastapi
# or
phlo plugin install fastapi
```

## Configuration

| Variable       | Default | Description |
| -------------- | ------- | ----------- |
| `FASTAPI_PORT` | `8000`  | API port    |

## Usage

```bash
phlo services start --service fastapi
```

## Endpoints

- **API**: `http://localhost:8000`
- **Docs**: `http://localhost:8000/docs`
