# scaffold (/docs/python-reference/packages/phlo-dlt/phlo_dlt/scaffold)



Workflow Scaffolding.

Generates Phlo workflow files from templates for DLT-based ingestion.
This module provides the scaffolding logic used by the CLI to create
initial file structures for new data pipelines.

Key Functions:

* :func:`create_ingestion_workflow`: Main scaffolding function
* :func:`parse_field_specs`: Parse CLI field specifications

Helper Functions:

* :func:`_to_snake_case`: Convert string to snake\_case
* :func:`_to_pascal_case`: Convert string to PascalCase

Data Structures:

* :class:`FieldSpec`: Parsed field specification dataclass

Type Mappings:
The following type names are supported in field specifications:

* `str`: String type
* `int`: Integer type
* `float`: Float type
* `bool`: Boolean type
* `datetime`: datetime.datetime (requires import)
* `date`: datetime.date (requires import)

Field Specification Syntax:
Fields are specified as `name:type` with optional modifiers:

* `name:type`: Required field
* `name:type?`: Nullable field
* `name:type!`: Required field (explicit)

Generated Files:

1. Schema file (`workflows/schemas/\{domain\}.py`):
   Pandera DataFrameModel with field definitions
2. Asset file (`workflows/ingestion/\{domain\}/\{table\}.py`):
   DLT ingestion asset with REST API source template
3. Test file (`tests/test_\{domain\}_\{table\}.py`):
   Unit tests for schema validation

See Also:

* :mod:`phlo_dlt.cli_workflow`: CLI command that uses this module
* :mod:`phlo_dlt.decorator`: The @phlo\_ingestion decorator used in templates
* Pandera documentation: [https://pandera.readthedocs.io/](https://pandera.readthedocs.io/)

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

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;FieldSpec&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dlt/phlo_dlt/scaffold/FieldSpec&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_to_snake_case&#x22;" type="&#x22;(name) -> str&#x22;">
      Convert string to snake\_case.

      Transforms a string into snake\_case format by:

      1. Replacing spaces and hyphens with underscores
      2. Inserting underscores between camelCase transitions
      3. Converting to lowercase

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        from phlo_dlt.scaffold import _to_snake_case

        _to_snake_case("WeatherData")  # "weather_data"
        _to_snake_case("API-Response")  # "api_response"
        _to_snake_case("some name")  # "some_name"
        ```
      </Callout>

      <PySourceCode>
        ````python
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
                \```python
                from phlo_dlt.scaffold import _to_snake_case

                _to_snake_case("WeatherData")  # "weather_data"
                _to_snake_case("API-Response")  # "api_response"
                _to_snake_case("some name")  # "some_name"
                \```

            """
            name = re.sub(r"[\s-]+", "_", name)
            name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
            return name.lower()
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Input string to convert.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        The snake\_case version of the input.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_to_pascal_case&#x22;" type="&#x22;(name) -> str&#x22;">
      Convert string to PascalCase.

      Transforms a string into PascalCase format by:

      1. Splitting on underscores, spaces, or hyphens
      2. Capitalizing each word
      3. Joining without separators

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        from phlo_dlt.scaffold import _to_pascal_case

        _to_pascal_case("weather_data")  # "WeatherData"
        _to_pascal_case("api-response")  # "ApiResponse"
        _to_pascal_case("some name")  # "SomeName"
        ```
      </Callout>

      <PySourceCode>
        ````python
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
                \```python
                from phlo_dlt.scaffold import _to_pascal_case

                _to_pascal_case("weather_data")  # "WeatherData"
                _to_pascal_case("api-response")  # "ApiResponse"
                _to_pascal_case("some name")  # "SomeName"
                \```

            """
            words = re.split(r"[_\s-]+", name)
            return "".join(word.capitalize() for word in words)
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Input string to convert.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        The PascalCase version of the input.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;parse_field_specs&#x22;" type="&#x22;(raw_specs) -> list[FieldSpec]&#x22;">
      Parse raw CLI field specifications.

      Parses field specifications from CLI input into structured FieldSpec objects.
      Validates type names and normalizes field names to snake\_case.

      <Callout title="&#x22;Field Specification Format&#x22;" type="&#x22;field-specification-format&#x22;">
        * `name:type`: Required field (implicit)
        * `name:type?`: Nullable field
        * `name:type!`: Required field (explicit)
        * Type must be one of: str, int, float, bool, datetime, date
      </Callout>

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```python
        from phlo_dlt.scaffold import parse_field_specs

        specs = parse_field_specs(["user_id:str", "age:int?", "email:str!"])
        # Returns: [FieldSpec("user_id", "str", False), FieldSpec("age", "int", True), ...]
        ```
      </Callout>

      <PySourceCode>
        ````python
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
                \```python
                from phlo_dlt.scaffold import parse_field_specs

                specs = parse_field_specs(["user_id:str", "age:int?", "email:str!"])
                # Returns: [FieldSpec("user_id", "str", False), FieldSpec("age", "int", True), ...]
                \```

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

                if not name or name in seen:
                    continue
                seen.add(name)
                fields.append(FieldSpec(name=name, type_name=type_part, nullable=nullable))

            return fields
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;raw_specs&#x22;" type="&#x22;list[str] | None&#x22;" value="undefined">
          Field specs in `name:type`, `name:type?`, or `name:type!` form.
          Examples: "user\_id:str", "age:int?", "email:str!"
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        list\[FieldSpec]: Parsed and normalized field specs.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;create_ingestion_workflow&#x22;" type="&#x22;(domain, table_name, unique_key, cron='0 */1 * * *', api_base_url=None, fields=None) -> List[str]&#x22;">
      Create ingestion workflow files.

      Generates a complete ingestion workflow scaffold including:

      1. Pandera schema definition file
      2. DLT ingestion asset file
      3. Unit test file

      Creates files in workflows/ and tests/ directories relative to
      the current working directory.

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
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
        print(f"Created: \{files\}")
        ```
      </Callout>

      <PySourceCode>
        ````python
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
                \```python
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
                \```

            """
            domain_snake = _to_snake_case(domain)
            table_snake = _to_snake_case(table_name)
            schema_class = f"Raw{_to_pascal_case(table_name)}"
            field_specs = parse_field_specs(fields)

            project_root = Path.cwd()

            schema_dir = project_root / "workflows" / "schemas"
            asset_dir = project_root / "workflows" / "ingestion" / domain_snake
            test_dir = project_root / "tests"
            schema_import_path = f"workflows.schemas.{domain_snake}"

            schema_file = schema_dir / f"{domain_snake}.py"
            asset_file = asset_dir / f"{table_snake}.py"
            test_file = test_dir / f"test_{domain_snake}_{table_snake}.py"

            existing = [str(f) for f in (schema_file, asset_file, test_file) if f.exists()]
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

            schema_fields_lines = [
                f'    {unique_key}: Series[str] = pa.Field(description="Unique key", nullable=False)'
            ]
            for field in field_specs:
                if field.name == unique_key:
                    continue
                schema_fields_lines.append(
                    f"    {field.name}: Series[{field.type_name}] = pa.Field(nullable={field.nullable})"
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
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;domain&#x22;" type="&#x22;str&#x22;" value="undefined">
          Domain/category name (e.g., "weather", "stripe"). Used for
          directory structure and group naming.
        </PyParameter>

        <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Target table name. Will be used for asset naming and
          file naming.
        </PyParameter>

        <PyParameter name="&#x22;unique_key&#x22;" type="&#x22;str&#x22;" value="undefined">
          Column name to use for deduplication and merge operations.
        </PyParameter>

        <PyParameter name="&#x22;cron&#x22;" type="&#x22;str&#x22;" value="&#x22;'0 */1 * * *'&#x22;">
          Cron schedule expression for automated runs.
          Default: "0 \*/1 \* \* \*" (hourly).
        </PyParameter>

        <PyParameter name="&#x22;api_base_url&#x22;" type="&#x22;Optional[str]&#x22;" value="&#x22;None&#x22;">
          Optional REST API base URL for the data source.
          If not provided, asset will raise RuntimeError until configured.
        </PyParameter>

        <PyParameter name="&#x22;fields&#x22;" type="&#x22;list[str] | None&#x22;" value="&#x22;None&#x22;">
          List of additional field specifications in "name:type" format.
          Example: \["temperature:float", "humidity:float?"]
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;typing.List&#x22;">
        List\[str]: Paths to created files (relative to project root):

        * workflows/schemas/\{domain}.py
        * workflows/ingestion/\{domain}/\{table}.py
        * tests/test\_\{domain}\_\{table}.py
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
