# Authorization

A user validates, plans, syncs, verifies, and reverts RBAC config (`roles.yaml` / `policies.yaml` under `.phlo`). Group `phlo authz`.

## Sub-features

- `validate` — `--path` directory containing RBAC config. `Validation passed.` exit 0, or `Validation failed:` + errors exit 1.
- `plan` — `--path --backend --environment` (read).
- `sync` — `--path --backend --environment --dry-run`. Real sync is a mutation.
- `verify` — compare backends to desired state.
- `revert` — `revert IDS --path --backend --environment` (mutation).

## How to get to it (user POV)

- `phlo authz --help`
- `phlo authz validate --path .phlo`
- `phlo authz plan`
- `phlo authz sync --dry-run` then `phlo authz sync`
- `phlo authz verify`

## Driving it with CLI

Preconditions:

- RBAC files present for validate. Default local verify often has none.
- `sync` without `--dry-run` and `revert` need authorization + real backends (**Docker** / OPA / IdP). `--dry-run` is the CLI-safe slice.

- Help: `uv run --locked phlo authz --help` → Commands `plan`, `revert`, `sync`, `validate`, `verify`.
- Validate missing/invalid: non-zero with listed errors; passed prints `Validation passed.`

## Gotchas

- `PHLO_AUTHORIZATION_MODE=optional` on phlo-api is not this CLI group.
- Do not sync against a shared cluster; v1 is single-tenant local.
