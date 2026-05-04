"""Workflow Scaffolding.

Generates Phlo workflow files from templates for DLT-based ingestion.
This module provides the scaffolding logic used by the CLI to create
initial file structures for new data pipelines.

Key Functions:
    - :func:`create_ingestion_workflow`: Main scaffolding function
    - :func:`parse_field_specs`: Parse CLI field specifications

Helper Functions:
    - :func:`_to_snake_case`: Convert string to snake_case
    - :func:`_to_pascal_case`: Convert string to PascalCase

Data Structures:
    - :class:`FieldSpec`: Parsed field specification dataclass

Type Mappings:
    The following type names are supported in field specifications:
    - ``str``: String type
    - ``int``: Integer type
    - ``float``: Float type
    - ``bool``: Boolean type
    - ``datetime``: datetime.datetime (requires import)
    - ``date``: datetime.date (requires import)

Field Specification Syntax:
    Fields are specified as ``name:type`` with optional modifiers:
    - ``name:type``: Required field
    - ``name:type?``: Nullable field
    - ``name:type!``: Required field (explicit)

Generated Files:
    1. Schema file (``workflows/schemas/{domain}.py``):
       Pandera DataFrameModel with field definitions
    2. Asset file (``workflows/ingestion/{domain}/{table}.py``):
       DLT ingestion asset with REST API source template
    3. Test file (``tests/test_{domain}_{table}.py``):
       Unit tests for schema validation

See Also:
    - :mod:`phlo_dlt.cli_workflow`: CLI command that uses this module
    - :mod:`phlo_dlt.decorator`: The @phlo_ingestion decorator used in templates
    - Pandera documentation: https://pandera.readthedocs.io/

Example:
    ```python
    from phlo_dlt.scaffold import create_ingestion_workflow

    files = create_ingestion_workflow(
        domain="weather",
        table_name="observations",
        unique_key="station_id",
        cron="0 */6 * * *",
        api_base_url="https://api.weather.com/v1",
        fields=["temperature:float", "humidity:float?", "recorded_at:datetime!"],
    )
    # Returns: ["workflows/schemas/weather.py", "workflows/ingestion/weather/observations.py", ...]
    ```

"""

from __future__ import annotations

from importlib.metadata import entry_points
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional


def _to_snake_case(name: str) -> str:
    """Convert string to snake_case.

    Transforms a string into snake_case format by:
    1. Replacing spaces and hyphens with underscores
    2. Inserting underscores between camelCase transitions
    3. Converting to lowercase

    Args:
        name: Input string to convert.

    Returns:
        str: The snake_case version of the input.

    Example:
        ```python
        from phlo_dlt.scaffold import _to_snake_case

        _to_snake_case("WeatherData")  # "weather_data"
        _to_snake_case("API-Response")  # "api_response"
        _to_snake_case("some name")  # "some_name"
        ```

    """
    name = re.sub(r"[\s-]+", "_", name)
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    return name.lower()


def _to_pascal_case(name: str) -> str:
    """Convert string to PascalCase.

    Transforms a string into PascalCase format by:
    1. Splitting on underscores, spaces, or hyphens
    2. Capitalizing each word
    3. Joining without separators

    Args:
        name: Input string to convert.

    Returns:
        str: The PascalCase version of the input.

    Example:
        ```python
        from phlo_dlt.scaffold import _to_pascal_case

        _to_pascal_case("weather_data")  # "WeatherData"
        _to_pascal_case("api-response")  # "ApiResponse"
        _to_pascal_case("some name")  # "SomeName"
        ```

    """
    words = re.split(r"[_\s-]+", name)
    return "".join(word.capitalize() for word in words)


@dataclass(frozen=True, slots=True)
class FieldSpec:
    """Structured representation of a scaffold field declaration.

    Immutable dataclass representing a parsed field specification with
    normalized name, type, and nullability information.

    Attributes:
        name: Normalized snake_case field name.
        type_name: Primitive field type name (str, int, float, bool, datetime, date).
        nullable: Whether the field is nullable (True for ? modifier).

    Example:
        ```python
        from phlo_dlt.scaffold import FieldSpec

        spec = FieldSpec(name="user_id", type_name="str", nullable=False)
        ```

    """

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


_MINIMAL_TEST_VALUES: dict[str, str] = {
    "str": '"test-001"',
    "int": "1",
    "float": "1.0",
    "bool": "True",
    "datetime": 'pd.Timestamp("2024-01-01T00:00:00Z")',
    "date": 'pd.Timestamp("2024-01-01").date()',
}


def _load_quality_provider() -> Any | None:
    """Load the active quality provider used for generated schemas."""
    try:
        from phlo.plugins.discovery import discover_plugins, get_quality_provider

        discover_plugins()
        provider = get_quality_provider("pandera")
        if provider is not None:
            return provider
    except Exception:
        pass

    try:
        providers = entry_points(group="phlo.plugins.quality_providers")
        for provider_entry in providers:
            if provider_entry.name != "pandera":
                continue
            return provider_entry.load()()
    except Exception:
        pass

    return None


def _resolve_schema_base_import() -> tuple[str, str]:
    """Resolve the generated schema base class from the active quality provider."""
    provider = _load_quality_provider()
    if provider is not None:
        schema_base_import = provider.get_schema_base_import()
        if schema_base_import is not None:
            return schema_base_import

    return ("pandera.pandas", "DataFrameModel")


def _render_schema_field(
    provider: Any | None,
    *,
    name: str,
    type_name: str,
    nullable: bool,
    description: str | None = None,
) -> str:
    """Render a generated schema field through the quality provider when available."""
    if provider is not None and hasattr(provider, "render_schema_field"):
        rendered = provider.render_schema_field(
            name=name,
            type_name=type_name,
            nullable=nullable,
            description=description,
        )
        if rendered is not None:
            return rendered

    description_arg = f'description="{description}", ' if description else ""
    return f"    {name}: Series[{type_name}] = pa.Field({description_arg}nullable={nullable})"


def _render_schema_module(
    provider: Any | None,
    *,
    domain: str,
    schema_class: str,
    schema_base_module: str,
    schema_base_name: str,
    type_imports: str,
    schema_fields: str,
) -> str:
    """Render a generated schema module through the quality provider when available."""
    if provider is not None and hasattr(provider, "render_schema_module"):
        rendered = provider.render_schema_module(
            domain=domain,
            schema_class=schema_class,
            type_imports=type_imports,
            schema_fields=schema_fields,
        )
        if rendered is not None:
            return rendered

    return f'''"""
Pandera schemas for {domain} domain.

Extend this schema with additional fields as you stabilize the source contract.
"""

{type_imports}import pandera as pa
from pandera.typing import Series
from {schema_base_module} import {schema_base_name}

class {schema_class}({schema_base_name}):
{schema_fields}

    class Config:
        strict = False
        coerce = True
'''


def _render_schema_class_block(
    *,
    schema_class: str,
    schema_base_name: str,
    schema_fields: str,
) -> str:
    """Render one schema class block for an existing schema module."""
    return f"""class {schema_class}({schema_base_name}):
{schema_fields}

    class Config:
        strict = False
        coerce = True
"""


def _append_missing_imports(path: Path, import_lines: str) -> None:
    """Append missing type imports to an existing generated schema module."""
    if not import_lines:
        return
    content = path.read_text()
    missing = [line for line in import_lines.splitlines() if line and line not in content]
    if not missing:
        return
    insertion = "\n".join(missing) + "\n"
    lines = content.splitlines(keepends=True)
    insert_at = 0
    for index, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            insert_at = index + 1
    lines.insert(insert_at, insertion)
    path.write_text("".join(lines))


def _append_schema_class(path: Path, schema_class: str, class_block: str) -> None:
    """Append a schema class to an existing schema file."""
    content = path.read_text()
    if re.search(rf"^class\s+{re.escape(schema_class)}\b", content, flags=re.MULTILINE):
        raise FileExistsError(f"Schema class already exists: {schema_class}")
    separator = "\n\n" if content.endswith("\n") else "\n\n\n"
    path.write_text(f"{content.rstrip()}{separator}{class_block}")


def _ensure_project_dependencies(project_root: Path, dependencies: tuple[str, ...]) -> None:
    """Ensure scaffold-required dependencies are present in project pyproject.toml."""
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        return
    content = pyproject.read_text()
    match = re.search(r"(?ms)^dependencies\s*=\s*\[(?P<body>.*?)^]", content)
    if not match:
        return
    body = match.group("body")
    missing = [
        dependency
        for dependency in dependencies
        if not re.search(rf'"\s*{re.escape(dependency)}\s*(?:[<>=!~\[]|")', body)
    ]
    if not missing:
        return
    additions = "".join(f'    "{dependency}",\n' for dependency in missing)
    insert_at = match.end("body")
    pyproject.write_text(f"{content[:insert_at]}{additions}{content[insert_at:]}")


def _minimal_test_value(type_name: str) -> str:
    """Return Python source for a minimal valid test value."""
    return _MINIMAL_TEST_VALUES.get(type_name, '"test-001"')


def parse_field_specs(raw_specs: list[str] | None) -> list[FieldSpec]:
    """Parse raw CLI field specifications.

    Parses field specifications from CLI input into structured FieldSpec objects.
    Validates type names and normalizes field names to snake_case.

    Args:
        raw_specs: Field specs in ``name:type``, ``name:type?``, or ``name:type!`` form.
            Examples: "user_id:str", "age:int?", "email:str!"

    Returns:
        list[FieldSpec]: Parsed and normalized field specs.

    Raises:
        ValueError: If any field spec format is invalid or type is not recognized.

    Field Specification Format:
        - ``name:type``: Required field (implicit)
        - ``name:type?``: Nullable field
        - ``name:type!``: Required field (explicit)
        - Type must be one of: str, int, float, bool, datetime, date

    Example:
        ```python
        from phlo_dlt.scaffold import parse_field_specs

        specs = parse_field_specs(["user_id:str", "age:int?", "email:str!"])
        # Returns: [FieldSpec("user_id", "str", False), FieldSpec("age", "int", True), ...]
        ```

    """
    if not raw_specs:
        return []

    fields: list[FieldSpec] = []
    seen: set[str] = set()
    for raw in raw_specs:
        raw = raw.strip()
        if not raw:
            continue

        if ":" not in raw:
            raise ValueError(f"Invalid field spec '{raw}'. Expected format name:type or name:type?")

        name, type_part = raw.split(":", 1)
        name = _to_snake_case(name)
        type_part = type_part.strip().lower()

        nullable = False
        if type_part.endswith("?"):
            nullable = True
            type_part = type_part[:-1]
        elif type_part.endswith("!"):
            type_part = type_part[:-1]

        if type_part not in _TYPE_IMPORTS:
            allowed = ", ".join(sorted(_TYPE_IMPORTS.keys()))
            raise ValueError(f"Invalid field type '{type_part}' for '{name}'. Allowed: {allowed}")

        if not name:
            continue
        if name in seen:
            raise ValueError(f"Duplicate field '{name}'")
        seen.add(name)
        fields.append(FieldSpec(name=name, type_name=type_part, nullable=nullable))

    return fields


def create_ingestion_workflow(
    domain: str,
    table_name: str,
    unique_key: str,
    cron: str = "0 */1 * * *",
    api_base_url: Optional[str] = None,
    fields: list[str] | None = None,
) -> List[str]:
    """Create ingestion workflow files.

    Generates a complete ingestion workflow scaffold including:
    1. Pandera schema definition file
    2. DLT ingestion asset file
    3. Unit test file

    Creates files in workflows/ and tests/ directories relative to
    the current working directory.

    Args:
        domain: Domain/category name (e.g., "weather", "stripe"). Used for
            directory structure and group naming.
        table_name: Target table name. Will be used for asset naming and
            file naming.
        unique_key: Column name to use for deduplication and merge operations.
        cron: Cron schedule expression for automated runs.
            Default: "0 */1 * * *" (hourly).
        api_base_url: Optional REST API base URL for the data source.
            If not provided, asset will raise RuntimeError until configured.
        fields: List of additional field specifications in "name:type" format.
            Example: ["temperature:float", "humidity:float?"]

    Returns:
        List[str]: Paths to created files (relative to project root):
            - workflows/schemas/{domain}.py
            - workflows/ingestion/{domain}/{table}.py
            - tests/test_{domain}_{table}.py

    Raises:
        FileExistsError: If any of the target files already exist.

    Example:
        ```python
        from phlo_dlt.scaffold import create_ingestion_workflow

        files = create_ingestion_workflow(
            domain="weather",
            table_name="observations",
            unique_key="station_id",
            cron="0 */6 * * *",
            api_base_url="https://api.weather.com/v1",
            fields=["temperature:float", "humidity:float?", "recorded_at:datetime"],
        )
        print(f"Created: {files}")
        ```

    """
    domain_snake = _to_snake_case(domain)
    table_snake = _to_snake_case(table_name)
    schema_class = f"Raw{_to_pascal_case(table_snake)}"
    field_specs = parse_field_specs(fields)

    project_root = Path.cwd()

    schema_dir = project_root / "workflows" / "schemas"
    asset_dir = project_root / "workflows" / "ingestion" / domain_snake
    test_dir = project_root / "tests"
    schema_import_path = f"workflows.schemas.{domain_snake}"

    schema_file = schema_dir / f"{domain_snake}.py"
    asset_file = asset_dir / f"{table_snake}.py"
    test_file = test_dir / f"test_{domain_snake}_{table_snake}.py"

    existing = [str(f) for f in (asset_file, test_file) if f.exists()]
    if existing:
        raise FileExistsError("Files already exist:\n" + "\n".join(f"  - {f}" for f in existing))

    asset_dir.mkdir(parents=True, exist_ok=True)
    test_dir.mkdir(parents=True, exist_ok=True)

    domain_init = asset_dir / "__init__.py"
    if not domain_init.exists():
        domain_init.write_text(f'"""Domain: {domain}"""\n')

    type_import_lines = sorted(
        {
            f"from {mod} import {sym}"
            for f in field_specs
            if (imp := _TYPE_IMPORTS[f.type_name]) and (mod := imp[0]) and (sym := imp[1])
        }
    )
    type_imports = "\n".join(type_import_lines)
    if type_imports:
        type_imports = f"{type_imports}\n\n"

    field_by_name = {field.name: field for field in field_specs}
    unique_key_normalized = _to_snake_case(unique_key)
    unique_key_field = field_by_name.get(unique_key_normalized)
    unique_key_type = unique_key_field.type_name if unique_key_field else "str"
    if unique_key_field and unique_key_field.nullable:
        raise ValueError(f"Unique key '{unique_key_normalized}' cannot be nullable")
    unique_key_nullable = False
    schema_provider = _load_quality_provider()
    schema_base_module, schema_base_name = _resolve_schema_base_import()

    schema_fields_lines = [
        _render_schema_field(
            schema_provider,
            name=unique_key_normalized,
            type_name=unique_key_type,
            nullable=unique_key_nullable,
            description="Unique key",
        )
    ]
    for field in field_specs:
        if field.name == unique_key_normalized:
            continue
        schema_fields_lines.append(
            _render_schema_field(
                schema_provider,
                name=field.name,
                type_name=field.type_name,
                nullable=field.nullable,
            )
        )

    schema_fields = "\n".join(schema_fields_lines)

    schema_content = _render_schema_module(
        schema_provider,
        domain=domain,
        schema_class=schema_class,
        schema_base_module=schema_base_module,
        schema_base_name=schema_base_name,
        type_imports=type_imports,
        schema_fields=schema_fields,
    )

    if schema_file.exists():
        _append_missing_imports(schema_file, type_imports)
        _append_schema_class(
            schema_file,
            schema_class,
            _render_schema_class_block(
                schema_class=schema_class,
                schema_base_name=schema_base_name,
                schema_fields=schema_fields,
            ),
        )
    else:
        schema_file.write_text(schema_content)

    _ensure_project_dependencies(project_root, ("phlo-dlt", "phlo-pandera"))

    base_url_literal = api_base_url or ""
    asset_content = f'''"""
{domain.capitalize()} {table_name} ingestion asset.

Ingests {table_name} from a REST API via `dlt.sources.rest_api`.
"""

from dlt.sources.rest_api import rest_api
from phlo_dlt import phlo_ingestion

from {schema_import_path} import {schema_class}


@phlo_ingestion(
    table_name="{table_snake}",
    unique_key="{unique_key_normalized}",
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
        client={{
            "base_url": base_url,
        }},
        resources=[
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
    )
'''

    asset_file.write_text(asset_content)

    extra_required_fields_lines = [
        f'        "{field.name}": {_minimal_test_value(field.type_name)},'
        for field in field_specs
        if not field.nullable and field.name != unique_key_normalized
    ]
    extra_required_fields = "\n".join(extra_required_fields_lines)
    if extra_required_fields:
        extra_required_fields = "\n" + extra_required_fields

    test_content = f'''"""
Tests for {domain} {table_name} scaffolded workflow.
"""

import pandas as pd

from {schema_import_path} import {schema_class}


def test_schema_contains_unique_key() -> None:
    schema_fields = {schema_class}.to_schema().columns.keys()
    assert "{unique_key_normalized}" in schema_fields


def test_schema_validates_minimal_row() -> None:
    df = pd.DataFrame(
        [
            {{
                "{unique_key_normalized}": {_minimal_test_value(unique_key_type)},{extra_required_fields}
            }}
        ]
    )
    validated = {schema_class}.validate(df)
    assert validated["{unique_key_normalized}"].iloc[0] == {_minimal_test_value(unique_key_type)}
'''

    test_file.write_text(test_content)

    return [
        str(schema_file.relative_to(project_root)),
        str(asset_file.relative_to(project_root)),
        str(test_file.relative_to(project_root)),
    ]
