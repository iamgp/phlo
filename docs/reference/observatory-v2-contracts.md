# Observatory v2 Contracts

Provider-neutral Observatory v2 contracts define how packages expose platform
capabilities to the Observatory UI without coupling the UI to provider-specific
APIs, credentials, URLs, or implementation details.

Audience: package authors and platform developers who contribute capabilities,
read models, UI surfaces, or guarded actions.

## Capability Inventory

`GET /api/observatory/v2/capability-inventory`

Returns the provider-neutral inventory of capabilities available to Observatory
v2 for the active project and runtime. The inventory is the UI's source of truth
for deciding which surfaces, read models, actions, and native escape hatches are
available.

Consumers should treat the endpoint as descriptive, not imperative:

- use it to discover contributed capabilities
- use it to decide which Observatory surfaces to show
- use it to bind UI contributions to read models and guarded actions
- do not infer provider internals from provider names, package names, or native
  service URLs

## UI Contributions

A UI contribution describes how one capability appears in Observatory v2.

Required and supported fields:

| Field | Description |
| --- | --- |
| `name` | Stable contribution name shown in diagnostics and inventory output. |
| `capability_type` | Capability category, such as data, assets, quality, storage, governance, or services. |
| `capability_name` | Stable capability identifier within the capability type. |
| `surfaces` | Observatory surfaces where the contribution may appear. |
| `read_models` | Provider-neutral read contracts that the UI may query for this contribution. |
| `actions` | Guarded v2 action contracts exposed for this contribution. |
| `native_links` | Declared provider-native escape hatches. Observatory currently suppresses emitted native links until a public link policy is defined. |
| `metadata` | Sanitized descriptive metadata for labels, grouping, filtering, and diagnostics. |

## Surfaces

Prefer existing Observatory v2 surfaces before introducing new ones:

- `Data`
- `Assets`
- `Runs`
- `Quality`
- `Changes`
- `Storage`
- `Observability`
- `Governance`
- `Catalog`
- `APIs`
- `BI`
- `Services`
- `Settings`

New surfaces should be reserved for capabilities that do not fit the existing
navigation model. A provider-specific product area is not, by itself, a reason
to add a surface.

## Metadata Rules

Metadata must be safe to return to the browser and safe to persist in logs,
diagnostics, screenshots, and support bundles.

Do not include:

- secrets
- passwords
- tokens
- raw provider URLs
- connection keys
- credentials
- private DSNs
- signed URLs
- provider-specific configuration values that grant access

Use metadata for neutral descriptors only, such as display labels, package
names, capability versions, supported modes, tags, and sanitized identifiers.

## Actions

Actions must use guarded Observatory v2 action contracts. A UI contribution may
advertise an action only when the action is represented by a v2 contract that
can describe:

- action identity
- target resource
- required parameters
- validation state
- safety guardrails
- execution status
- user-visible result or failure reason

Actions should not expose raw provider commands, shell commands, credentials,
or direct provider API calls to the UI.

## Native Links

Native links may eventually point users to provider-native tools when Observatory
does not yet cover a workflow or when the native tool remains the best place for
deep inspection. The current v2 inventory contract accepts declared native links
but suppresses them in browser payloads until a public link policy is defined.

Native links are escape hatches. They must not replace provider-neutral read
models, Observatory surfaces, or guarded v2 actions for core workflows.

Native link labels and destinations must not disclose credentials, embedded
tokens, private connection strings, or raw internal provider URLs.
