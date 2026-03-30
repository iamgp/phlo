# Production Readiness

Use this checklist before treating a Phlo stack as production-capable.

## Checklist

- configuration is explicit and environment-specific
- secrets are not left at defaults
- storage, catalog, and metadata services have backup and recovery plans
- observability is enabled and routed to a real backend
- API surfaces are intentionally chosen, not all enabled by default
- access controls are defined for users and services
- data quality and promotion gates are enforced
- runbooks exist for startup, shutdown, migration, and incident response

## Readiness Domains

### Runtime

- service topology is pinned and understood
- ports and profiles are documented
- health checks are verified

### Data

- medallion or equivalent lifecycle is explicit
- schemas and migrations are versioned
- recovery path from raw or bronze is understood

### Observability

- traces, metrics, and logs are emitted
- dashboards or query paths exist for key incidents
- alerting path is defined where needed

### Access

- default credentials are removed
- authn/authz model is chosen per exposed surface
- serving surfaces are exposed intentionally

## Related Pages

- [Operations Guide](operations-guide.md)
- [Security](../setup/security.md)
- [Observability](../setup/observability.md)
- [Deployment Profiles](../guides/deployment-profiles.md)
