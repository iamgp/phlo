# phlo-hasura (/docs/packages/phlo-hasura)



Overview [#overview]

`phlo-hasura` exposes PostgreSQL tables as a GraphQL API with real-time subscriptions.

Installation [#installation]

```bash
pip install phlo-hasura
# or
phlo plugin install hasura
```

Profile [#profile]

Part of the `api` profile.

Configuration [#configuration]

| Variable              | Default                    | Description             |
| --------------------- | -------------------------- | ----------------------- |
| `HASURA_PORT`         | `8082`                     | Hasura console/API port |
| `HASURA_VERSION`      | `v2.46.0`                  | Hasura version          |
| `HASURA_ADMIN_SECRET` | `phlo-hasura-admin-secret` | Admin secret            |

Features [#features]

Auto-Configuration [#auto-configuration]

| Feature            | How It Works                                            |
| ------------------ | ------------------------------------------------------- |
| **Table Tracking** | Auto-tracks tables in `api` schema via post\_start hook |
| **Metrics Labels** | Exposes Hasura metrics at `/v1/metrics`                 |
| **Anonymous Role** | Configured with `anonymous` role for public access      |

Post-Start Hook [#post-start-hook]

```yaml
hooks:
  post_start:
    - name: track-tables
      command: python -m phlo_hasura.hooks track-tables auto
```

Usage [#usage]

Starting the Service [#starting-the-service]

```bash
# Start with API profile
phlo services start --profile api

# Or start individually
phlo services start --service hasura
```

GraphQL Examples [#graphql-examples]

```graphql
# Query marts data
query GetDailySummary {
  mrt_daily_summary(order_by: { date: desc }, limit: 10) {
    date
    total_count
    average_value
  }
}

# Filter data
query GetHighValues {
  mrt_daily_summary(where: { average_value: { _gt: 100 } }) {
    date
    average_value
  }
}

# Aggregation
query GetStats {
  mrt_daily_summary_aggregate {
    aggregate {
      count
      avg {
        average_value
      }
      max {
        average_value
      }
    }
  }
}

# Real-time subscription
subscription WatchData {
  mrt_daily_summary(order_by: { date: desc }, limit: 5) {
    date
    total_count
  }
}
```

cURL Examples [#curl-examples]

```bash
# Query with admin secret
curl -X POST http://localhost:8082/v1/graphql \
  -H "X-Hasura-Admin-Secret: phlo-hasura-admin-secret" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ mrt_daily_summary(limit: 5) { date total_count } }"}'
```

Endpoints [#endpoints]

| Endpoint    | URL                                |
| ----------- | ---------------------------------- |
| **GraphQL** | `http://localhost:8082/v1/graphql` |
| **Console** | `http://localhost:8082/console`    |
| **Metrics** | `http://localhost:8082/v1/metrics` |

Entry Points [#entry-points]

| Entry Point             | Plugin                |
| ----------------------- | --------------------- |
| `phlo.plugins.services` | `HasuraServicePlugin` |
| `phlo.plugins.cli`      | Hasura CLI commands   |

Related Packages [#related-packages]

* [phlo-postgres](phlo-postgres.md) - Database service
* [phlo-postgrest](phlo-postgrest.md) - REST alternative
* [phlo-api](phlo-api.md) - Custom API endpoints

Next Steps [#next-steps]

* [Hasura Setup](../setup/hasura.md) - Complete configuration
* [API Reference](../reference/phlo-api.md) - API documentation
