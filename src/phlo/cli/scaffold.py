"""
Workflow Scaffolding

Generates Phlo workflow files from templates.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


def _to_snake_case(name: str) -> str:
    """Convert string to snake_case."""
    # Replace spaces and hyphens with underscores
    name = re.sub(r"[\s-]+", "_", name)
    # Insert underscore before capital letters
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    return name.lower()


def _to_pascal_case(name: str) -> str:
    """Convert string to PascalCase."""
    # Split on underscores, hyphens, and spaces
    words = re.split(r"[_\s-]+", name)
    return "".join(word.capitalize() for word in words)


@dataclass(frozen=True, slots=True)
class FieldSpec:
    name: str
    type_name: str
    nullable: bool


_TYPE_IMPORTS: dict[str, tuple[str, str] | None] = {
    "str": None,
    "int": None,
    "float": None,
    "bool": None,
    "datetime": ("datetime", "datetime"),
    "date": ("datetime", "date"),
}


def parse_field_specs(raw_specs: list[str] | None) -> list[FieldSpec]:
    if not raw_specs:
        return []

    fields: list[FieldSpec] = []
    for raw in raw_specs:
        raw = raw.strip()
        if not raw:
            continue

        if ":" not in raw:
            raise ValueError(f"Invalid field spec '{raw}'. Expected format name:type or name:type?")

        name, type_part = raw.split(":", 1)
        name = _to_snake_case(name)
        type_part = type_part.strip().lower()

        nullable = True
        if type_part.endswith("?"):
            nullable = True
            type_part = type_part[:-1]
        elif type_part.endswith("!"):
            nullable = False
            type_part = type_part[:-1]

        if type_part not in _TYPE_IMPORTS:
            allowed = ", ".join(sorted(_TYPE_IMPORTS.keys()))
            raise ValueError(f"Invalid field type '{type_part}' for '{name}'. Allowed: {allowed}")

        fields.append(FieldSpec(name=name, type_name=type_part, nullable=nullable))

    seen: set[str] = set()
    deduped: list[FieldSpec] = []
    for field in fields:
        if not field.name or field.name in seen:
            continue
        seen.add(field.name)
        deduped.append(field)

    return deduped


def _series_type(type_name: str) -> str:
    mapping = {
        "str": "str",
        "int": "int",
        "float": "float",
        "bool": "bool",
        "datetime": "datetime",
        "date": "date",
    }
    return mapping[type_name]


def create_ingestion_workflow(
    domain: str,
    table_name: str,
    unique_key: str,
    cron: str = "0 */1 * * *",
    api_base_url: Optional[str] = None,
    fields: list[str] | None = None,
) -> List[str]:
    """
    Create ingestion workflow files.

    Creates files in workflows/ and tests/ for the current project.

    Args:
        domain: Domain name (e.g., "weather", "stripe")
        table_name: Table name (e.g., "observations", "charges")
        unique_key: Unique key field for deduplication
        cron: Cron schedule expression
        api_base_url: REST API base URL (optional)

    Returns:
        List of created file paths

    Raises:
        FileExistsError: If files already exist
        ValueError: If invalid parameters
    """
    # Normalize names
    domain_snake = _to_snake_case(domain)
    table_snake = _to_snake_case(table_name)
    schema_class = f"Raw{_to_pascal_case(table_name)}"
    field_specs = parse_field_specs(fields)

    project_root = Path.cwd()

    # Phlo core no longer owns workflow modules; always scaffold into workflows/.
    schema_dir = project_root / "workflows" / "schemas"
    asset_dir = project_root / "workflows" / "ingestion" / domain_snake
    test_dir = project_root / "tests"
    schema_import_path = f"workflows.schemas.{domain_snake}"

    schema_file = schema_dir / f"{domain_snake}.py"
    asset_file = asset_dir / f"{table_snake}.py"
    test_file = test_dir / f"test_{domain_snake}_{table_snake}.py"

    # Check if files already exist
    existing = []
    if schema_file.exists():
        existing.append(str(schema_file))
    if asset_file.exists():
        existing.append(str(asset_file))
    if test_file.exists():
        existing.append(str(test_file))

    if existing:
        raise FileExistsError("Files already exist:\n" + "\n".join(f"  - {f}" for f in existing))

    # Create directories
    asset_dir.mkdir(parents=True, exist_ok=True)
    test_dir.mkdir(parents=True, exist_ok=True)

    # Create __init__.py for domain if needed
    domain_init = asset_dir / "__init__.py"
    if not domain_init.exists():
        domain_init.write_text(f'"""Domain: {domain}"""\n')

    # Generate schema file
    type_import_lines: list[str] = []
    for field in field_specs:
        import_spec = _TYPE_IMPORTS[field.type_name]
        if import_spec is not None:
            module, symbol = import_spec
            type_import_lines.append(f"from {module} import {symbol}")

    type_imports = "\n".join(sorted(set(type_import_lines)))
    if type_imports:
        type_imports = f"{type_imports}\n\n"

    schema_fields_lines = [
        f'    {unique_key}: Series[str] = pa.Field(description="Unique key", nullable=False)'
    ]
    for field in field_specs:
        if field.name == unique_key:
            continue
        schema_fields_lines.append(
            f"    {field.name}: Series[{_series_type(field.type_name)}] = "
            f"pa.Field(nullable={field.nullable})"
        )

    schema_fields = "\n".join(schema_fields_lines)

    schema_content = f'''"""
Pandera schemas for {domain} domain.

Extend this schema with additional fields as you stabilize the source contract.
"""

import pandera as pa
from pandera.typing import Series

{type_imports}class {schema_class}(pa.DataFrameModel):
{schema_fields}

    class Config:
        strict = False
        coerce = True
'''

    schema_file.write_text(schema_content)

    # Generate asset file
    base_url_literal = api_base_url or ""
    asset_content = f'''"""
{domain.capitalize()} {table_name} ingestion asset.

Ingests {table_name} from a REST API via `dlt.sources.rest_api`.
"""

from dlt.sources.rest_api import rest_api

from phlo_dlt import phlo_ingestion
from {schema_import_path} import {schema_class}


@phlo_ingestion(
    table_name="{table_name}",
    unique_key="{unique_key}",
    validation_schema={schema_class},
    group="{domain_snake}",
    cron="{cron}",
    freshness_hours=(1, 24),
)
def {table_snake}(partition_date: str):
    start_time = f"{{partition_date}}T00:00:00.000Z"
    end_time = f"{{partition_date}}T23:59:59.999Z"

    base_url = "{base_url_literal}"
    if not base_url:
        raise RuntimeError(
            "Missing API base URL. Re-run scaffold with --api-base-url or set it in the asset."
        )

    return rest_api(
        {{
            "client": {{
                "base_url": base_url,
            }},
            "resources": [
                {{
                    "name": "{table_snake}",
                    "endpoint": {{
                        "path": "{table_name}",
                        "params": {{
                            "start_date": start_time,
                            "end_date": end_time,
                        }},
                    }},
                }}
            ],
        }}
    )
'''

    asset_file.write_text(asset_content)

    # Generate test file
    test_content = f'''"""
Tests for {domain} {table_name} scaffolded workflow.
"""

import pandas as pd

from {schema_import_path} import {schema_class}


def test_schema_contains_unique_key() -> None:
    schema_fields = {schema_class}.to_schema().columns.keys()
    assert "{unique_key}" in schema_fields


def test_schema_validates_minimal_row() -> None:
    df = pd.DataFrame([{{"{unique_key}": "test-001"}}])
    validated = {schema_class}.validate(df)
    assert validated["{unique_key}"].iloc[0] == "test-001"
'''

    test_file.write_text(test_content)

    return [
        str(schema_file.relative_to(project_root)),
        str(asset_file.relative_to(project_root)),
        str(test_file.relative_to(project_root)),
    ]
