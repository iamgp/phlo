# cli_schema_utils (/docs/python-reference/packages/phlo-pandera/phlo_pandera/cli_schema_utils)



Shared CLI utilities for schema commands.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_default_schema_search_paths&#x22;" type="&#x22;() -> list[str]&#x22;">
      Return default schema search paths rooted at the project when available.

      <PySourceCode>
        ```python
        def _default_schema_search_paths() -> list[str]:
            """Return default schema search paths rooted at the project when available.

            Returns:
                List of search path strings. Uses PHLO_SCHEMA_SEARCH_PATHS env var
                if set, otherwise defaults to examples/ and workflows/ directories.

            """
            env_paths = os.getenv("PHLO_SCHEMA_SEARCH_PATHS")
            if env_paths:
                return [path.strip() for path in env_paths.split(",") if path.strip()]

            project_root = os.getenv("PHLO_PROJECT_PATH")
            if project_root:
                return [
                    str(Path(project_root) / "examples"),
                    str(Path(project_root) / "workflows"),
                ]

            return ["examples", "workflows"]
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;list&#x22;">
        List of search path strings. Uses PHLO\_SCHEMA\_SEARCH\_PATHS env var
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;format_table&#x22;" type="&#x22;(title, columns, rows) -> Table&#x22;">
      Create a Rich Table with given data.

      <PySourceCode>
        ```python
        def format_table(title: str, columns: list[str], rows: list[tuple]) -> Table:
            """Create a Rich Table with given data.

            Args:
                title: Table title.
                columns: List of column headers.
                rows: List of tuples (one per row).

            Returns:
                Rich Table instance with data populated.

            """
            table = Table(title=title)
            for col in columns:
                table.add_column(col)
            for row in rows:
                table.add_row(*[str(item) for item in row])
            return table
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;title&#x22;" type="&#x22;str&#x22;" value="undefined">
          Table title.
        </PyParameter>

        <PyParameter name="&#x22;columns&#x22;" type="&#x22;list[str]&#x22;" value="undefined">
          List of column headers.
        </PyParameter>

        <PyParameter name="&#x22;rows&#x22;" type="&#x22;list[tuple]&#x22;" value="undefined">
          List of tuples (one per row).
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;rich.table.Table&#x22;">
        Rich Table instance with data populated.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;discover_pandera_schemas&#x22;" type="&#x22;(search_paths=None) -> dict[str, type]&#x22;">
      Discover all Pandera DataFrameModel subclasses.

      Scans specified directories for schema definitions and loads them.

      <PySourceCode>
        ```python
        def discover_pandera_schemas(
            search_paths: Optional[list[str]] = None,
        ) -> dict[str, type]:
            """
            Discover all Pandera DataFrameModel subclasses.

            Scans specified directories for schema definitions and loads them.

            Args:
                search_paths: List of paths to search (default: examples/ and workflows/)
                    or comma-separated PHLO_SCHEMA_SEARCH_PATHS environment variable.

            Returns:
                Dictionary mapping schema name to schema class

            """
            import inspect
            from importlib import import_module

            from pandera.pandas import DataFrameModel

            if search_paths is None:
                search_paths = _default_schema_search_paths()

            schemas = {}

            for search_path in search_paths:
                path = Path(search_path)
                if not path.exists():
                    continue

                for py_file in path.glob("**/schemas/*.py"):
                    if py_file.name.startswith("_"):
                        continue

                    try:
                        parts = py_file.relative_to(path.parent).parts[:-1] + (py_file.stem,)
                        module_name = ".".join(parts)

                        try:
                            module = import_module(module_name)
                        except (ImportError, ModuleNotFoundError):
                            logger.debug(
                                "schema_discovery_import_failed",
                                module_name=module_name,
                            )
                            continue

                        for name, obj in inspect.getmembers(module):
                            if (
                                inspect.isclass(obj)
                                and issubclass(obj, DataFrameModel)
                                and obj is not DataFrameModel
                            ):
                                schemas[name] = obj

                    except Exception:
                        logger.warning(
                            "schema_discovery_file_scan_failed",
                            search_path=str(path),
                            schema_file=str(py_file),
                        )
                        continue

            return schemas
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;search_paths&#x22;" type="&#x22;Optional[list[str]]&#x22;" value="&#x22;None&#x22;">
          List of paths to search (default: examples/ and workflows/)
          or comma-separated PHLO\_SCHEMA\_SEARCH\_PATHS environment variable.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Dictionary mapping schema name to schema class
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;classify_schema_change&#x22;" type="&#x22;(old_schema, new_schema) -> tuple[str, list[str]]&#x22;">
      Classify schema changes as SAFE, WARNING, or BREAKING.

      <PySourceCode>
        ```python
        def classify_schema_change(old_schema: dict, new_schema: dict) -> tuple[str, list[str]]:
            """
            Classify schema changes as SAFE, WARNING, or BREAKING.

            Args:
                old_schema: Original schema (dict of column_name -> type)
                new_schema: New schema (dict of column_name -> type)

            Returns:
                Tuple of (classification, details_list)

            """
            old_cols = set(old_schema.keys())
            new_cols = set(new_schema.keys())

            added = new_cols - old_cols
            removed = old_cols - new_cols
            changed = old_cols & new_cols

            details = []
            severity = "SAFE"

            if removed:
                details.append(f"Removed columns: {', '.join(removed)}")
                severity = "BREAKING"

            type_changes = []
            for col in changed:
                if old_schema[col] != new_schema[col]:
                    type_changes.append(f"{col}: {old_schema[col]} -> {new_schema[col]}")

            if type_changes:
                details.append(f"Type changes: {', '.join(type_changes)}")
                severity = "BREAKING"

            if added:
                details.append(f"Added columns: {', '.join(added)}")
                if severity == "SAFE":
                    severity = "SAFE"

            if not details:
                details.append("No changes detected")

            return severity, details
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;old_schema&#x22;" type="&#x22;dict&#x22;" value="undefined">
          Original schema (dict of column\_name -> type)
        </PyParameter>

        <PyParameter name="&#x22;new_schema&#x22;" type="&#x22;dict&#x22;" value="undefined">
          New schema (dict of column\_name -> type)
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;tuple&#x22;">
        Tuple of (classification, details\_list)
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
