# phlo-hasura

Hasura GraphQL API service plugin for Phlo.

## Description

GraphQL API engine with real-time subscriptions over PostgreSQL.

## Installation

```bash
pip install phlo-hasura
# or
phlo plugin install hasura
```

## Configuration

| Variable      | Default | Description      |
| ------------- | ------- | ---------------- |
| `HASURA_PORT` | `8081`  | GraphQL API port |

## Usage

```bash
phlo services start --service hasura
```

## Dependencies

- postgres

## Endpoints

- **GraphQL**: `http://localhost:8081/v1/graphql`
- **Console**: `http://localhost:8081/console`
