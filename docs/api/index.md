# API Reference

This section contains API documentation for Cascade's programmatic interfaces.

## FastAPI REST API

The FastAPI service provides REST endpoints for data access and system operations.

- **Base URL**: http://localhost:10010
- **Documentation**: http://localhost:10010/docs (Swagger UI)
- **ReDoc**: http://localhost:10010/redoc

## Hasura GraphQL API

The Hasura service provides GraphQL access to PostgreSQL data.

- **Base URL**: http://localhost:10011
- **Console**: http://localhost:10011/console
- **GraphQL Endpoint**: http://localhost:10011/v1/graphql

## Authentication

Both APIs support JWT-based authentication. Obtain tokens from the FastAPI `/auth/login` endpoint.

## Examples

```python
import requests

# FastAPI example
response = requests.get("http://localhost:10010/health")
print(response.json())

# GraphQL example
query = """
query GetTables {
  tables: information_schema_tables {
    table_name
    table_schema
  }
}
"""

response = requests.post(
    "http://localhost:10011/v1/graphql",
    json={"query": query},
    headers={"Authorization": "Bearer YOUR_JWT_TOKEN"}
)
print(response.json())
```
