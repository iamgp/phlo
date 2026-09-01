#!/usr/bin/env bash
# Prove CLI-only identity + plugin check + support/audit/governance JSON contracts.
# Contract: exit 0 when --help lists core groups, plugin check invalid=[], extra JSON parses.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"
cd "${REPO_ROOT}"

export PATH="${HOME}/.local/bin:${PATH}"

RUN_ID="${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)-$$}"
EVIDENCE_DIR="${REPO_ROOT}/.cursor/skills/verify-phlo/artifacts/runs/${RUN_ID}"
EXAMPLE="${REPO_ROOT}/.cursor/skills/verify-phlo/artifacts/cli-surface.example.md"

mkdir -p "${EVIDENCE_DIR}"

{
  echo "cwd=$(pwd)"
  uv run --locked phlo --version
  set +e
  uv run --locked phlo doctor --json
  echo "doctor_exit=$?"
  set -e
} >"${EVIDENCE_DIR}/doctor.txt" 2>&1

uv run --locked phlo --help >"${EVIDENCE_DIR}/help.txt"

set +e
uv run --locked phlo plugin check --json >"${EVIDENCE_DIR}/plugin-check.json" 2>"${EVIDENCE_DIR}/plugin-check.stderr"
check_rc=$?
uv run --locked phlo support status --json >"${EVIDENCE_DIR}/support.json" 2>"${EVIDENCE_DIR}/support.stderr"
support_rc=$?
uv run --locked phlo audit tail --json --limit 1 >"${EVIDENCE_DIR}/audit.json" 2>"${EVIDENCE_DIR}/audit.stderr"
audit_rc=$?
uv run --locked phlo governance check --json >"${EVIDENCE_DIR}/governance.json" 2>"${EVIDENCE_DIR}/governance.stderr"
gov_rc=$?
uv run --locked phlo plugin list --type cli --json >"${EVIDENCE_DIR}/plugin-cli.json" 2>"${EVIDENCE_DIR}/plugin-cli.stderr"
list_rc=$?
set -e

{
  echo "plugin_check_exit=${check_rc}"
  echo "support_exit=${support_rc}"
  echo "audit_exit=${audit_rc}"
  echo "governance_exit=${gov_rc}"
  echo "plugin_list_cli_exit=${list_rc}"
} >"${EVIDENCE_DIR}/action.txt"

python3 - "${EVIDENCE_DIR}" <<'PY'
import json
import sys
from pathlib import Path

evidence = Path(sys.argv[1])
help_text = (evidence / "help.txt").read_text()
required = [
    "init",
    "doctor",
    "support",
    "test",
    "audit",
    "logs",
    "services",
    "workflow",
    "plugin",
    "schema-migrate",
    "migrate",
    "metrics",
    "contracts",
    "config",
    "env",
    "authz",
    "compliance",
    "governance",
    "materialize",
    "status",
]
missing = [name for name in required if name not in help_text]
if missing:
    raise SystemExit(f"phlo --help missing commands: {missing}")

check = json.loads((evidence / "plugin-check.json").read_text())
if check.get("invalid") != []:
    raise SystemExit(f"plugin check invalid: {check.get('invalid')}")
if not check.get("valid"):
    raise SystemExit("plugin check valid list empty")

support = json.loads((evidence / "support.json").read_text())
for key in ("compatible", "items", "gates"):
    if key not in support:
        raise SystemExit(f"support json missing {key}")

audit = json.loads((evidence / "audit.json").read_text())
if audit.get("errors") != []:
    raise SystemExit(f"audit errors: {audit.get('errors')}")
if "items" not in audit.get("data", {}):
    raise SystemExit("audit envelope missing data.items")

gov = json.loads((evidence / "governance.json").read_text())
if "ok" not in gov:
    raise SystemExit("governance json missing ok")

plugins = json.loads((evidence / "plugin-cli.json").read_text())
names = {item["name"] for item in plugins.get("installed", [])}
expected = {
    "alerts",
    "clickhouse",
    "clickstack",
    "dagster",
    "dbt",
    "dlt",
    "hasura",
    "lineage",
    "mcp",
    "minio",
    "nessie",
    "openmetadata",
    "postgres",
    "postgrest",
    "quality",
    "sling",
    "trino",
}
missing_plugins = sorted(expected - names)
if missing_plugins:
    raise SystemExit(f"cli plugins missing: {missing_plugins}")
print("cli_surface_ok")
PY

cat >"${EVIDENCE_DIR}/summary.md" <<EOF
# cli-surface proof

- RUN_ID: ${RUN_ID}
- phlo --help lists core groups from src/phlo/cli/main.py plus plugin roots
- plugin check --json: invalid=[] valid nonempty (exit ${check_rc})
- support status --json parsed (exit ${support_rc}; 1 is expected when extra packages are unexpected)
- audit tail --json empty items (exit ${audit_rc})
- governance check --json (exit ${gov_rc})
- plugin list --type cli --json has 17 workspace CLI plugins
- Docker: not used
EOF

cp "${EVIDENCE_DIR}/summary.md" "${EXAMPLE}"
{
  echo
  echo "## plugin-check.json (truncated)"
  echo
  echo '```json'
  python3 -c "import json,pathlib; p=pathlib.Path('${EVIDENCE_DIR}/plugin-check.json'); d=json.loads(p.read_text()); print(json.dumps({'invalid':d['invalid'],'valid_count':len(d['valid']),'valid_head':d['valid'][:8]}, indent=2))"
  echo '```'
  echo
  echo "## support.json (truncated)"
  echo
  echo '```json'
  python3 -c "import json,pathlib; d=json.loads(pathlib.Path('${EVIDENCE_DIR}/support.json').read_text()); print(json.dumps({'compatible':d['compatible'],'production_ready':d.get('production_ready'),'gates':d['gates'],'item_count':len(d['items'])}, indent=2))"
  echo '```'
  echo
  echo "## plugin list --type cli names"
  echo
  echo '```'
  python3 -c "import json,pathlib; d=json.loads(pathlib.Path('${EVIDENCE_DIR}/plugin-cli.json').read_text()); print('\n'.join(sorted(x['name'] for x in d['installed'])))"
  echo '```'
} >>"${EXAMPLE}"

echo "evidence=${EVIDENCE_DIR}"
echo "example=${EXAMPLE}"
