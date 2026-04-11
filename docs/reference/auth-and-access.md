# Auth And Access Model

Authentication and authorization in Phlo are layered.

## Model

```mermaid
flowchart TD
    principal["User or service principal"] --> authn["Authentication provider"]
    authn --> session["Authenticated session"]
    session --> authz["Authorization policy backend"]
    authz --> surfaces["API and UI surfaces"]
    authz --> data["Data and governance backends"]
```

## Responsibilities

- authentication decides who the caller is
- authorization decides what that caller may do
- serving layers like `phlo-api`, `Hasura`, and `PostgREST` enforce those decisions in different ways
- governance and backend systems may apply their own secondary controls

## phlo-api Route Guard Semantics

- `phlo-api` route guards only enforce authorization when an authorization backend is configured
- with the default `PHLO_AUTHORIZATION_MODE=optional`, guarded routes remain reachable when `PHLO_AUTHORIZATION_BACKEND` is unset
- set `PHLO_AUTHORIZATION_MODE=required` to fail closed with HTTP `503` on guarded routes when no authorization backend is configured
- once a backend is configured, route guards evaluate the caller normally and still return `401` or `403` based on authentication and policy decisions

You can declare these settings in `phlo.yaml` as either:

```yaml
api:
  authorization:
    backend: opa
    mode: required
```

or, for a service-scoped override:

```yaml
services:
  phlo-api:
    authorization:
      backend: opa
      mode: required
```

Precedence is `env vars` -> `services.phlo-api.authorization` -> `api.authorization`.

## Canonical RBAC

- canonical RBAC currently supports `allow` policies only
- canonical `deny` rules are rejected by `phlo authz validate` and backend planning
- do not model deny semantics in `.phlo/authorization/policies.yaml` until backend compilation support exists

## Where To Look

- [Security](../setup/security.md) for operator setup and posture
- [Python Reference](../python-reference/index.mdx) for capability-level auth interfaces
- [API Surfaces](api-surfaces.md) for how access shows up across external entry points
