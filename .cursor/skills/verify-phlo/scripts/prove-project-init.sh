#!/usr/bin/env bash
# Prove project-init for verify-phlo: isolated tmp project, evidence kept, tmp removed.
# Contract: exit 0 only when csv-batch (or PHLO_VERIFY_TEMPLATE) files exist and JSON envelope is clean.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"
cd "${REPO_ROOT}"

export PATH="${HOME}/.local/bin:${PATH}"

RUN_ID="${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)-$$}"
TEMPLATE="${PHLO_VERIFY_TEMPLATE:-csv-batch}"
PROJECT_ROOT="/tmp/phlo-verify-${RUN_ID}"
PROJECT="${PROJECT_ROOT}/my-lakehouse"
EVIDENCE_DIR="${REPO_ROOT}/.cursor/skills/verify-phlo/artifacts/runs/${RUN_ID}"
EXAMPLE="${REPO_ROOT}/.cursor/skills/verify-phlo/artifacts/project-init.example.md"

mkdir -p "${EVIDENCE_DIR}" "${PROJECT_ROOT}"

cleanup_project() {
  rm -rf "${PROJECT_ROOT}"
}

trap cleanup_project EXIT

{
  echo "cwd=$(pwd)"
  echo "python=$(python3 -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])')"
  command -v uv
  uv run --locked phlo --version
  echo "--- leftover /tmp/phlo-verify-* ---"
  ls -d /tmp/phlo-verify-* 2>/dev/null || echo "(none besides this run)"
  echo "--- phlo doctor --json ---"
  set +e
  uv run --locked phlo doctor --json
  doctor_rc=$?
  set -e
  echo "doctor_exit=${doctor_rc}"
} >"${EVIDENCE_DIR}/doctor.txt" 2>&1

action_log="${EVIDENCE_DIR}/action.txt"
{
  echo "command=uv run --locked phlo init ${PROJECT} --template ${TEMPLATE} --json"
  echo "cwd=${REPO_ROOT}"
} >"${action_log}"

set +e
uv run --locked phlo init "${PROJECT}" --template "${TEMPLATE}" --json >"${EVIDENCE_DIR}/init.json" 2>"${EVIDENCE_DIR}/init.stderr"
init_rc=$?
set -e

{
  echo "exit_code=${init_rc}"
  echo "--- stdout ---"
  cat "${EVIDENCE_DIR}/init.json"
  echo "--- stderr ---"
  cat "${EVIDENCE_DIR}/init.stderr"
} >>"${action_log}"

if [[ "${init_rc}" -ne 0 ]]; then
  echo "phlo init failed with ${init_rc}" >&2
  trap - EXIT
  exit "${init_rc}"
fi

python3 - "${EVIDENCE_DIR}/init.json" "${PROJECT}" "${TEMPLATE}" <<'PY'
import json
import sys
from pathlib import Path

payload_path, project, template = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
payload = json.loads(Path(payload_path).read_text())
if payload.get("errors"):
    raise SystemExit(f"init envelope errors: {payload['errors']}")
data = payload["data"]
if data["template"] != template:
    raise SystemExit(f"template {data['template']!r} != {template!r}")
if data["project_dir"] != str(project):
    raise SystemExit(f"project_dir {data['project_dir']!r} != {str(project)!r}")

required = [
    project / "phlo.yaml",
    project / "pyproject.toml",
    project / "workflows" / "__init__.py",
]
if template == "csv-batch":
    required.extend(
        [
            project / "data" / "events.csv",
            project / "workflows" / "ingestion" / "csv" / "events.py",
            project / "workflows" / "schemas" / "csv.py",
        ]
    )
missing = [str(path) for path in required if not path.is_file()]
if missing:
    raise SystemExit(f"missing generated files: {missing}")

yaml_text = (project / "phlo.yaml").read_text()
if "name:" not in yaml_text:
    raise SystemExit("phlo.yaml missing name:")
if template == "csv-batch":
    events = (project / "workflows" / "ingestion" / "csv" / "events.py").read_text()
    if "@phlo.ingestion(" not in events:
        raise SystemExit("csv-batch workflow missing @phlo.ingestion(")
print("side_effects_ok")
PY

(
  echo "project=${PROJECT}"
  find "${PROJECT}" -type f | sort
) >"${EVIDENCE_DIR}/tree.txt"

cat >"${EVIDENCE_DIR}/summary.md" <<EOF
# project-init proof

- RUN_ID: ${RUN_ID}
- template: ${TEMPLATE}
- isolated project: ${PROJECT} (removed after copy)
- evidence: \`.cursor/skills/verify-phlo/artifacts/runs/${RUN_ID}/\`
- init exit: 0
- side effects: phlo.yaml, pyproject.toml, csv-batch workflow files present
- Docker: not required for this feature
EOF

cp "${EVIDENCE_DIR}/summary.md" "${EXAMPLE}"
{
  echo
  echo "## init.json"
  echo
  echo '```json'
  cat "${EVIDENCE_DIR}/init.json"
  echo '```'
  echo
  echo "## tree"
  echo
  echo '```'
  cat "${EVIDENCE_DIR}/tree.txt"
  echo '```'
  echo
  echo "## doctor (truncated)"
  echo
  echo '```'
  head -n 40 "${EVIDENCE_DIR}/doctor.txt"
  echo '```'
} >>"${EXAMPLE}"

echo "evidence=${EVIDENCE_DIR}"
echo "example=${EXAMPLE}"
echo "project_removed_on_exit=${PROJECT_ROOT}"
