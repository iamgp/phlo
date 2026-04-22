# Setup

Use this section when you are exposing a platform surface, enabling a cross-cutting capability, or wiring Phlo into a wider environment.

These guides focus on the operational decisions and configuration that turn a running stack into something users, tools, or other systems can interact with.

## What You Will Find Here

- [Hasura](hasura.md): expose GraphQL over warehouse data, track tables, and define permissions.
- [PostgREST](postgrest.md): expose a database-native REST surface with roles, JWT, and schema controls.
- [OpenMetadata](openmetadata.md): register services, ingest metadata, and make the catalog searchable.
- [Observability](observability.md): route logs, traces, and metrics into the observability backend you want to run.
- [Security](security.md): apply authentication, secrets, and security posture across the stack.
- [Service Credentials](service-credentials.md): move regulated deployments off shared backend admin credentials.
- [Canonical RBAC](../reference/canonical-rbac.md): define source-of-truth roles and policies before wiring backend-specific authorization.

## Typical Uses

Most teams will only need a subset of these pages. A common path is:

1. install the packages and start the base stack
2. decide which external surfaces you want to expose
3. configure auth, metadata, and observability for that environment
4. return to [Guides](../guides/index.md) for workflow patterns and developer tasks

For package-by-package component details, use [Packages](../packages/index.md). For commands, flags, and canonical behavior, use [Reference](../reference/index.md).
