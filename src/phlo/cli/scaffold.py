"""
Workflow Scaffolding

Generates Cascade workflow files from templates.
"""

import re
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


def _is_user_project(project_root: Path) -> bool:
    """
    Detect if this is a user project or the Cascade repository.

    Returns:
        True if user project, False if Cascade repo
    """
    # User projects have workflows/ directory but not src/phlo/
    has_workflows = (project_root / "workflows").exists()
    has_cascade_src = (project_root / "src" / "phlo").exists()

    # If both exist, prefer user project mode
    if has_workflows and not has_cascade_src:
        return True
    elif has_workflows and has_cascade_src:
        # Both exist - check pyproject.toml to determine
        pyproject = project_root / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            # User projects have "phlo" as a dependency
            # Cascade repo has name = "phlo"
            if 'name = "phlo"' in content:
                return False  # Cascade repo
        return True  # User project
    else:
        return False  # Cascade repo


def create_ingestion_workflow(
    domain: str,
    table_name: str,
    unique_key: str,
    cron: str = "0 */1 * * *",
    api_base_url: Optional[str] = None,
) -> List[str]:
    """
    Create ingestion workflow files.

    Automatically detects project type:
    - User project: Creates files in workflows/
    - Cascade repo: Creates files in src/phlo/defs/

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

    project_root = Path.cwd()

    # Detect project type
    is_user_project = _is_user_project(project_root)

    # Define paths based on project type
    if is_user_project:
        # User project mode - use workflows/
        schema_dir = project_root / "workflows" / "schemas"
        asset_dir = project_root / "workflows" / "ingestion" / domain_snake
        test_dir = project_root / "tests"
        schema_import_path = f"workflows.schemas.{domain_snake}"
    else:
        # Cascade repo mode - use src/phlo/defs/
        schema_dir = project_root / "src" / "phlo" / "schemas"
        asset_dir = project_root / "src" / "phlo" / "defs" / "ingestion" / domain_snake
        test_dir = project_root / "tests"
        schema_import_path = f"phlo.schemas.{domain_snake}"

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
    schema_content = f'''"""
Pandera schemas for {domain} domain.

Schemas define data validation rules and auto-generate Iceberg schemas.
"""

import pandera as pa
from pandera.typing import Series


class {schema_class}(pa.DataFrameModel):
    """
    Raw {table_name} data schema.

    TODO: Add your schema fields here. Examples:

    # String field (required)
    {unique_key}: Series[str] = pa.Field(description="Unique identifier", nullable=False)

    # Numeric field with constraints
    # value: Series[float] = pa.Field(ge=0, le=100, description="Value between 0-100")

    # Timestamp field
    # timestamp: Series[str] = pa.Field(description="ISO 8601 timestamp")

    # Optional field
    # notes: Series[str] = pa.Field(nullable=True, description="Optional notes")

    # Boolean field
    # is_active: Series[bool] = pa.Field(description="Active status")
    """

    {unique_key}: Series[str] = pa.Field(
        description="Unique identifier for deduplication",
        nullable=False,
    )

    # TODO: Add your fields below

    class Config:
        """Pandera config."""
        strict = True  # Reject extra columns
        coerce = True  # Coerce types when possible
'''

    schema_file.write_text(schema_content)

    # Generate asset file
    asset_content = f'''"""
{domain.capitalize()} {table_name} ingestion asset.

Ingests {table_name} from REST API to Iceberg.
"""

from dlt.sources.rest_api import rest_api
from phlo.ingestion import phlo_ingestion
from {schema_import_path} import {schema_class}


@phlo_ingestion(
    table_name="{table_name}",
    unique_key="{unique_key}",
    validation_schema={schema_class},
    group="{domain_snake}",
    cron="{cron}",
    freshness_hours=(1, 24),  # Warn if > 1 hour old, fail if > 24 hours
)
def {table_snake}(partition_date: str):
    """
    Ingest {table_name} for a given partition date.

    Args:
        partition_date: Date in YYYY-MM-DD format

    Returns:
        DLT source containing {table_name} data
    """
    # Format date range for partition
    start_time = f"{{partition_date}}T00:00:00.000Z"
    end_time = f"{{partition_date}}T23:59:59.999Z"

    # TODO: Configure your REST API source
    source = rest_api({{
        "client": {{
            "base_url": "{api_base_url or "https://api.example.com/v1"}",

            # TODO: Add authentication
            # "auth": {{
            #     "token": os.getenv("API_TOKEN"),
            # }},
        }},
        "resources": [{{
            "name": "{table_snake}",
            "endpoint": {{
                "path": "{table_name}",  # TODO: Update API endpoint path
                "params": {{
                    "start_date": start_time,
                    "end_date": end_time,
                    # TODO: Add other parameters
                }},
            }},
            # TODO: Add pagination if needed
            # "paginator": {{
            #     "type": "offset",
            #     "limit": 1000,
            # }},
        }}],
    }})

    return source
'''

    asset_file.write_text(asset_content)

    # Generate test file
    test_content = f'''"""
Tests for {domain} {table_name} workflow.
"""

import pytest
import pandas as pd
from {schema_import_path} import {schema_class}


class TestSchema:
    """Test Pandera schema validation."""

    def test_valid_data_passes_validation(self):
        """Test that valid data passes schema validation."""

        test_data = pd.DataFrame([
            {{
                "{unique_key}": "test-001",
                # TODO: Add test data for your fields
            }},
        ])

        # Should not raise
        validated = {schema_class}.validate(test_data)
        assert len(validated) == 1
        assert validated["{unique_key}"].iloc[0] == "test-001"

    def test_unique_key_field_exists(self):
        """Test that unique_key field exists in schema."""

        schema_fields = {schema_class}.to_schema().columns.keys()
        assert "{unique_key}" in schema_fields, \\
            f"unique_key '{unique_key}' not found. Available: {{list(schema_fields)}}"

    # TODO: Add more schema tests
    # def test_invalid_data_fails_validation(self):
    #     \"\"\"Test that invalid data fails validation.\"\"\"
    #     test_data = pd.DataFrame([{{
    #         "{unique_key}": "test",
    #         "value": -10,  # Violates constraints
    #     }}])
    #
    #     with pytest.raises(Exception):
    #         {schema_class}.validate(test_data)


# TODO: Add asset execution tests
# from phlo.testing import test_asset_execution
# from phlo.defs.ingestion.{domain_snake}.{table_snake} import {table_snake}
#
# def test_asset_with_mock_data():
#     \"\"\"Test asset execution with mock data.\"\"\"
#     test_data = [{{"
#         "{unique_key}": "1",
#         # Add fields
#     }}]
#
#     result = test_asset_execution(
#         asset_fn={table_snake},
#         partition="2024-01-15",
#         mock_data=test_data,
#         validation_schema={schema_class},
#     )
#
#     assert result.success
#     assert len(result.data) == 1
'''

    test_file.write_text(test_content)

    return [
        str(schema_file.relative_to(project_root)),
        str(asset_file.relative_to(project_root)),
        str(test_file.relative_to(project_root)),
    ]
