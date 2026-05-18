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

## Endpoint Families

All Observatory v2 endpoints are rooted at `/api/observatory/v2`. They are grouped by product surface rather than by provider package.

| Family | Endpoints | Contract intent |
| --- | --- | --- |
| Runtime overview | `overview`, `capabilities`, `capability-inventory` | Tell the browser what the active project can show and do. |
| Services and operations | `services`, `services/{service_id}`, `operations`, `operations/{operation_id}`, `runs` | Expose runtime health, service details, operator workflows, and run state. |
| Data and assets | `assets`, `assets/{asset_id}`, `tables`, `table-preview/{table_id}`, `query`, `saved-queries`, `stage-diff`, `row-journey/{table_id}/{row_id}` | Expose provider-neutral asset, table, query, diff, and row provenance read models. |
| Quality and logs | `quality`, `quality/{check_id}`, `logs`, `logs/facets` | Support quality triage and evidence inspection. |
| Branches and changes | `branches`, `branches/{branch_name}`, `branches/actions` | Describe branch state and execute guarded branch operations. |
| Capability surfaces | `storage`, `observability`, `governance`, `catalog`, `apis`, `bi` | Allow packages to contribute specialized operator surfaces without hardcoding provider APIs in the UI. |
| Extensions and settings | `extensions`, `extensions/{extension_id}`, `settings`, `search`, `actions` | Expose extension inventory, global search, settings state, and generic guarded actions. |

Route parameters that identify assets, tables, services, branches, and checks are stable resource identifiers, not provider URLs or secret-bearing connection strings.

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

Surface visibility should be capability-driven. For example, a Branches/Changes
view should only appear when a branching or catalog provider contributes the
corresponding read models and actions. Do not promote a route into primary
navigation just because an endpoint exists.

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

Action endpoints:

- `POST /api/observatory/v2/actions` for generic v2 action contracts
- `POST /api/observatory/v2/branches/actions` for branch-specific guarded actions

Both endpoints should return user-visible status and failure reasons that are
safe to display in browser UI and support bundles.

## Operation Journal

Observatory v2 records guarded action outcomes in the provider-neutral operation
journal at `.phlo/observatory-v2/operation_journal.json` for the active project.
The journal is exposed through `GET /api/observatory/v2/operations` and
`GET /api/observatory/v2/operations/{operation_id}`.

Journaled operations use the same `V2Operation` contract as provider-backed
maintenance read models. Action outcomes may have `succeeded`, `failed`, or
`skipped` status. A skipped operation means Observatory declined the action
because the required provider contract, capability, service state, or guardrail
was not available.

Operation metadata follows the standard v2 metadata rules. It may include safe
values such as action id, action kind, risk level, required capability, message,
recorded timestamp, and affected file paths. It must not include secrets,
provider credentials, private connection strings, raw provider URLs, or signed
URLs.

## Native Links

Native links may eventually point users to provider-native tools when Observatory
does not yet cover a workflow or when the native tool remains the best place for
deep inspection. The current v2 inventory contract accepts declared native links
but suppresses them in browser payloads until a public link policy is defined.

Native links are escape hatches. They must not replace provider-neutral read
models, Observatory surfaces, or guarded v2 actions for core workflows.

Native link labels and destinations must not disclose credentials, embedded
tokens, private connection strings, or raw internal provider URLs.
