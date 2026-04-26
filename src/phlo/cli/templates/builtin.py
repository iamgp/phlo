from __future__ import annotations

from pathlib import Path

from phlo.cli.templates.models import TemplateMetadata, TemplateRenderContext


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _build_env_example_content() -> str:
    from phlo.plugins.discovery import ServiceDiscovery

    lines = [
        "# Phlo Local Secrets Template",
        "# Copy to .phlo/.env.local after running `phlo services init`.",
        "",
    ]

    discovery = ServiceDiscovery()
    services = discovery.discover()
    if not services:
        lines.append(
            "# No service plugins discovered; install service packages to populate secrets."
        )
        return "\n".join(lines) + "\n"

    for service in sorted(services.values(), key=lambda item: item.name):
        secrets = {key: cfg for key, cfg in service.env_vars.items() if cfg.get("secret") is True}
        if not secrets:
            continue
        lines.append(f"# {service.name}")
        for key in sorted(secrets.keys()):
            desc = secrets[key].get("description")
            if desc:
                lines.append(f"# {desc}")
            lines.append(f"{key}=")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _pyproject_toml(project_name: str, required_packages: tuple[str, ...]) -> str:
    dependencies = "\n".join(f'    "{package}",' for package in required_packages)
    return f"""[project]
name = "{project_name}"
version = "0.1.0"
description = "Phlo data workflows"
requires-python = ">=3.11"
dependencies = [
{dependencies}
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "ruff",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I"]
"""


def _write_pyproject_toml(
    project_dir: Path, project_name: str, required_packages: tuple[str, ...]
) -> None:
    _write_text(project_dir / "pyproject.toml", _pyproject_toml(project_name, required_packages))


def _write_common_project_files(
    project_dir: Path, project_name: str, required_packages: tuple[str, ...]
) -> None:
    _write_text(
        project_dir / ".env.example",
        _build_env_example_content(),
    )
    _write_pyproject_toml(project_dir, project_name, required_packages)
    _write_text(
        project_dir / ".gitignore",
        """.env
.env.local
.phlo/
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
*.egg-info/
dist/
build/
.pytest_cache/
.coverage
htmlcov/
.ruff_cache/
""",
    )
    _write_text(
        project_dir / "README.md",
        f"""# {project_name}

Phlo data workflows for {project_name}.

## Getting Started

1. **Install dependencies:**
   ```bash
   pip install -e .
   ```

2. **Create your first workflow:**
   ```bash
   phlo workflow create
   ```

3. **Start Dagster UI:**
   ```bash
   phlo dev
   ```

4. **Access the UI:**
   Open http://localhost:3000 in your browser

## Project Structure

```
{project_name}/
├── workflows/          # Your workflow definitions
│   ├── ingestion/     # Data ingestion workflows
│   ├── schemas/       # Pandera validation schemas
│   └── transforms/dbt/ # dbt transformation models
└── tests/            # Workflow tests
```

## Documentation

- [Phlo Documentation](https://github.com/iamgp/phlo)
- [Workflow Development Guide](https://github.com/iamgp/phlo/blob/main/docs/guides/workflow-development.md)

## Commands

- `phlo dev` - Start Dagster development server
- `phlo workflow create` - Scaffold new workflow
- `phlo test` - Run tests
""",
    )

    from phlo.cli.commands.services.utils import PHLO_CONFIG_TEMPLATE

    _write_text(
        project_dir / "phlo.yaml",
        PHLO_CONFIG_TEMPLATE.format(
            name=project_name,
            description=f"{project_name} data workflows",
        ),
    )


class MinimalTemplate:
    metadata = TemplateMetadata(
        name="minimal",
        description="Empty Phlo project",
        required_packages=("phlo",),
        generated_paths=(
            "phlo.yaml",
            "pyproject.toml",
            ".env.example",
            ".gitignore",
            "README.md",
            "workflows/__init__.py",
            "tests/__init__.py",
        ),
        next_steps=("phlo services init", "phlo workflow create"),
    )

    def render(self, context: TemplateRenderContext) -> None:
        context.project_dir.mkdir(parents=True, exist_ok=True)
        workflows_dir = context.project_dir / "workflows"
        _write_text(workflows_dir / "__init__.py", '"""User workflows."""\n')
        _write_text(workflows_dir / "ingestion" / "__init__.py", '"""Ingestion workflows."""\n')
        _write_text(
            workflows_dir / "schemas" / "__init__.py",
            '"""Pandera validation schemas."""\n',
        )
        _write_text(context.project_dir / "tests" / "__init__.py", "")
        _write_common_project_files(
            context.project_dir, context.project_name, self.metadata.required_packages
        )


class BasicTemplate:
    metadata = TemplateMetadata(
        name="basic",
        description="dbt-ready Phlo project",
        required_packages=("phlo", "phlo-dbt"),
        generated_paths=(
            "phlo.yaml",
            "pyproject.toml",
            "workflows/transforms/dbt/dbt_project.yml",
        ),
        next_steps=("phlo services init", "phlo workflow create"),
    )

    def render(self, context: TemplateRenderContext) -> None:
        MinimalTemplate().render(context)
        _write_pyproject_toml(
            context.project_dir, context.project_name, self.metadata.required_packages
        )
        from phlo_dbt.scaffold import write_dbt_scaffold

        transforms_dir = context.project_dir / "workflows" / "transforms" / "dbt"
        write_dbt_scaffold(context.project_name, transforms_dir, context.project_dir)
        _write_text(transforms_dir / "models" / ".gitkeep", "")


class CsvBatchTemplate:
    metadata = TemplateMetadata(
        name="csv-batch",
        description="Local CSV batch pipeline",
        required_packages=("phlo", "phlo-dlt", "phlo-pandera"),
        generated_paths=(
            "data/events.csv",
            "workflows/ingestion/csv/events.py",
            "workflows/schemas/csv.py",
        ),
        next_steps=(
            "phlo test",
            "phlo materialize dlt_events",
        ),
    )

    def render(self, context: TemplateRenderContext) -> None:
        MinimalTemplate().render(context)
        _write_pyproject_toml(
            context.project_dir, context.project_name, self.metadata.required_packages
        )
        _write_text(
            context.project_dir / "data" / "events.csv",
            "id,name,value\n1,alpha,10\n2,beta,20\n",
        )
        _write_text(
            context.project_dir / "workflows" / "schemas" / "csv.py",
            """from __future__ import annotations

import pandera.pandas as pa


class EventsSchema(pa.DataFrameModel):
    id: int
    name: str
    value: int
""",
        )
        _write_text(
            context.project_dir / "workflows" / "ingestion" / "csv" / "events.py",
            """from __future__ import annotations

from pathlib import Path

import pandas as pd
import phlo

from workflows.schemas.csv import EventsSchema


@phlo.ingestion(table_name="events", unique_key="id", validation_schema=EventsSchema, group="csv")
def csv_events():
    return pd.read_csv(Path("data/events.csv"))
""",
        )


class ApiIngestionTemplate:
    metadata = TemplateMetadata(
        name="api-ingestion",
        description="REST API ingestion pipeline",
        required_packages=("phlo", "phlo-dlt", "phlo-pandera"),
        generated_paths=(
            "workflows/ingestion/api/events.py",
            "workflows/schemas/api.py",
        ),
        next_steps=(
            "phlo test",
            "phlo materialize dlt_events",
        ),
    )

    def render(self, context: TemplateRenderContext) -> None:
        MinimalTemplate().render(context)
        _write_pyproject_toml(
            context.project_dir, context.project_name, self.metadata.required_packages
        )
        _write_text(
            context.project_dir / "workflows" / "schemas" / "api.py",
            """from __future__ import annotations

import pandera.pandas as pa


class EventsSchema(pa.DataFrameModel):
    id: int
    name: str
""",
        )
        _write_text(
            context.project_dir / "workflows" / "ingestion" / "api" / "events.py",
            """from __future__ import annotations

import pandas as pd
import phlo

from workflows.schemas.api import EventsSchema


@phlo.ingestion(table_name="events", unique_key="id", validation_schema=EventsSchema, group="api")
def api_events():
    return pd.DataFrame([{"id": 1, "name": "sample"}])
""",
        )


class DbtMedallionTemplate:
    metadata = TemplateMetadata(
        name="dbt-medallion",
        description="Bronze/silver/gold dbt project",
        required_packages=("phlo", "phlo-dbt"),
        generated_paths=("workflows/transforms/dbt/models/silver/stg_events.sql",),
        next_steps=("dbt compile", "phlo services restart dagster"),
    )

    def render(self, context: TemplateRenderContext) -> None:
        BasicTemplate().render(context)
        base = context.project_dir / "workflows" / "transforms" / "dbt" / "models"
        _write_text(base / "bronze" / "source_events.sql", "select 1 as id, 'sample' as name\n")
        _write_text(
            base / "silver" / "stg_events.sql",
            "select id, name from {{ ref('source_events') }}\n",
        )
        _write_text(
            base / "gold" / "dim_events.sql",
            "select id, name from {{ ref('stg_events') }}\n",
        )
        _write_text(base / "sources.yml", "version: 2\nsources: []\n")


class SlingReplicationTemplate:
    metadata = TemplateMetadata(
        name="sling-replication",
        description="Sling replication starter",
        required_packages=("phlo", "phlo-sling"),
        generated_paths=("replication/sling.yaml",),
        next_steps=("phlo sling --help",),
    )

    def render(self, context: TemplateRenderContext) -> None:
        MinimalTemplate().render(context)
        _write_pyproject_toml(
            context.project_dir, context.project_name, self.metadata.required_packages
        )
        _write_text(
            context.project_dir / "replication" / "sling.yaml",
            """source: LOCAL
target: POSTGRES
streams:
  file://data/events.csv:
    object: public.events
""",
        )
        _write_text(context.project_dir / "data" / "events.csv", "id,name\n1,alpha\n")


class ObservabilityDemoTemplate:
    metadata = TemplateMetadata(
        name="observability-demo",
        description="Pipeline with telemetry wiring",
        required_packages=("phlo", "phlo-dlt", "phlo-pandera", "phlo-otel"),
        generated_paths=("workflows/ingestion/observability/events.py",),
        next_steps=("phlo services init", "phlo services start --profile observability"),
    )

    def render(self, context: TemplateRenderContext) -> None:
        CsvBatchTemplate().render(context)
        _write_pyproject_toml(
            context.project_dir, context.project_name, self.metadata.required_packages
        )
        _write_text(
            context.project_dir / "workflows" / "ingestion" / "observability" / "events.py",
            """from __future__ import annotations

import logging

import pandas as pd
import phlo

from workflows.schemas.csv import EventsSchema

logger = logging.getLogger(__name__)


@phlo.ingestion(
    table_name="observability_events",
    unique_key="id",
    validation_schema=EventsSchema,
    group="observability",
)
def observability_events():
    logger.info("loading observability demo events")
    return pd.DataFrame([{"id": 1, "name": "traceable", "value": 1}])
""",
        )
