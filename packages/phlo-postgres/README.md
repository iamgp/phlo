# phlo-postgres

PostgreSQL database service plugin for Phlo.

## Description

Provides PostgreSQL as a Docker-based service for metadata and operational storage.

## Installation

```bash
pip install phlo-postgres
# or
phlo plugin install postgres
```

## Configuration

| Variable            | Default | Description       |
| ------------------- | ------- | ----------------- |
| `POSTGRES_USER`     | `phlo`  | Database username |
| `POSTGRES_PASSWORD` | `phlo`  | Database password |
| `POSTGRES_DB`       | `phlo`  | Database name     |
| `POSTGRES_PORT`     | `5432`  | Host port         |

## Usage

Once installed, the service is automatically discovered by Phlo:

```bash
phlo services start --service postgres
```
