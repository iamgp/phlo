# Observatory (secondary)

Observatory is the web UI for inspecting a running lakehouse. It is **not** the primary verification surface. Reach it only after generated services include Observatory and `phlo-api`. Do not expand Observatory product docs here.

## Sub-features

- `api-health` — `phlo-api` HTTP `/health` (default port from `PHLO_API_PORT` / service, commonly 4000 in the package README).
- `ui` — Observatory HTTP (package README default `OBSERVATORY_PORT` 3001) after `phlo services start --service observatory`.
- `cli-equivalent` — same user jobs as CLI: assets (`phlo status` / `materialize`), tables (`phlo catalog tables`), lineage (`phlo lineage show`), services (`phlo services status`).

## How to get to it (user POV)

- `phlo plugin install observatory` or workspace `phlo-observatory` already installed.
- `phlo services init` (Observatory is a default local service in init’s help text) then **Docker**: `phlo services start --service observatory` and `phlo services start --service phlo-api` (or full start).
- Browser: Observatory UI; API docs at phlo-api `/docs`.

## Driving it with CLI

Preconditions:

- `.phlo/docker-compose.yml` includes observatory/api. **Docker required.** CLI-only verify uses the equivalent CLI features instead.

- Confirm generate: after `phlo services init --no-dev`, compose file exists and lists observatory/api service names if those plugins are installed (parse YAML; do not grep Dockerfiles for behavior).
- Live: `curl -sf http://127.0.0.1:$PHLO_API_PORT/health` only if this run started phlo-api. Then open the UI port. Tear down with `phlo services stop`.

**Not live-proven on a Docker-less VM.** Prefer [cli-identity.md](cli-identity.md), [project-init.md](project-init.md), [plugin-check.md](plugin-check.md).

## Gotchas

- Observatory reads phlo-api; a pretty UI with a dead API is not proof.
- Dev mounts: `phlo services init --dev --phlo-source <repo>` then start observatory.
- Do not treat marketing/docs sites as this surface.
