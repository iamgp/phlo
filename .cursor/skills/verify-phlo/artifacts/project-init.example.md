# project-init proof

- RUN_ID: 20260901T224815Z-3361
- template: csv-batch
- isolated project: /tmp/phlo-verify-20260901T224815Z-3361/my-lakehouse (removed after copy)
- evidence: `.cursor/skills/verify-phlo/artifacts/runs/20260901T224815Z-3361/`
- init exit: 0
- side effects: phlo.yaml, pyproject.toml, csv-batch workflow files present
- Docker: not required for this feature

## init.json

```json
{
  "data": {
    "generated_paths": [
      "data/events.csv",
      "workflows/ingestion/csv/events.py",
      "workflows/schemas/csv.py"
    ],
    "next_steps": [
      "cd /tmp/phlo-verify-20260901T224815Z-3361/my-lakehouse",
      "uv pip install -e .",
      "phlo services init",
      "phlo services start",
      "phlo doctor",
      "phlo test",
      "phlo materialize dlt_events --partition 2025-01-15"
    ],
    "project_dir": "/tmp/phlo-verify-20260901T224815Z-3361/my-lakehouse",
    "project_name": "my-lakehouse",
    "template": "csv-batch"
  },
  "errors": [],
  "warnings": []
}
```

## tree

```
project=/tmp/phlo-verify-20260901T224815Z-3361/my-lakehouse
/tmp/phlo-verify-20260901T224815Z-3361/my-lakehouse/AGENTS.md
/tmp/phlo-verify-20260901T224815Z-3361/my-lakehouse/contracts/.gitkeep
/tmp/phlo-verify-20260901T224815Z-3361/my-lakehouse/data/events.csv
/tmp/phlo-verify-20260901T224815Z-3361/my-lakehouse/data/.gitkeep
/tmp/phlo-verify-20260901T224815Z-3361/my-lakehouse/.env.example
/tmp/phlo-verify-20260901T224815Z-3361/my-lakehouse/.gitignore
/tmp/phlo-verify-20260901T224815Z-3361/my-lakehouse/phlo.yaml
/tmp/phlo-verify-20260901T224815Z-3361/my-lakehouse/plugins/.gitkeep
/tmp/phlo-verify-20260901T224815Z-3361/my-lakehouse/pyproject.toml
/tmp/phlo-verify-20260901T224815Z-3361/my-lakehouse/README.md
/tmp/phlo-verify-20260901T224815Z-3361/my-lakehouse/tests/__init__.py
/tmp/phlo-verify-20260901T224815Z-3361/my-lakehouse/workflows/ingestion/csv/events.py
/tmp/phlo-verify-20260901T224815Z-3361/my-lakehouse/workflows/ingestion/__init__.py
/tmp/phlo-verify-20260901T224815Z-3361/my-lakehouse/workflows/__init__.py
/tmp/phlo-verify-20260901T224815Z-3361/my-lakehouse/workflows/schemas/csv.py
/tmp/phlo-verify-20260901T224815Z-3361/my-lakehouse/workflows/schemas/__init__.py
```

## doctor (truncated)

```
cwd=/workspace
python=3.12.3
/home/ubuntu/.local/bin/uv
phlo, version 0.14.0
--- leftover /tmp/phlo-verify-* ---
/tmp/phlo-verify-20260901T224815Z-3361
--- phlo doctor --json ---
{
  "checks": [
    {
      "group": "Environment",
      "id": "doctor.bootstrap",
      "message": "Doctor command loaded",
      "status": "ok"
    },
    {
      "group": "Environment",
      "id": "env.python",
      "message": "Python 3.12.3",
      "status": "ok"
    },
    {
      "group": "Environment",
      "id": "env.uv",
      "message": "uv found",
      "status": "ok"
    },
    {
      "group": "Environment",
      "id": "env.container_backend",
      "message": "Container backend: docker",
      "status": "ok"
    },
    {
      "fix": "Install Docker Desktop or ensure docker is on PATH.",
      "group": "Environment",
      "id": "env.docker.cli",
      "message": "Docker CLI not found",
      "status": "fail"
    },
```
