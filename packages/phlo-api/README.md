# phlo-api

Backend API service for Phlo Observatory.

## Description

FastAPI-based backend service exposing Phlo internals to the Observatory UI. Provides endpoints for lineage, quality checks, assets, and metadata.

## Installation

```bash
pip install phlo-api
# or
phlo plugin install api
```

## Configuration

| Variable        | Default   | Description     |
| --------------- | --------- | --------------- |
| `PHLO_API_PORT` | `4000`    | API server port |
| `HOST`          | `0.0.0.0` | API server host |

## Auto-Configuration

This package is **fully auto-configured**:

| Feature               | How It Works                                            |
| --------------------- | ------------------------------------------------------- |
| **Metrics Labels**    | Exposes Prometheus metrics at `/metrics`                |
| **Service Discovery** | Automatically scraped by Prometheus                     |
| **Health Check**      | Provides `/health` endpoint for container orchestration |

## Usage

```bash
# Start the API service
phlo services start --service phlo-api

# Or run in dev mode
phlo services start --dev
```

## Endpoints

- **API Base**: `http://localhost:4000`
- **Health**: `http://localhost:4000/health`
- **Metrics**: `http://localhost:4000/metrics`
- **OpenAPI Docs**: `http://localhost:4000/docs`

## API Routes

| Route           | Description               |
| --------------- | ------------------------- |
| `/api/lineage`  | Data lineage queries      |
| `/api/quality`  | Quality check results     |
| `/api/assets`   | Dagster asset information |
| `/api/branches` | Nessie branch management  |
