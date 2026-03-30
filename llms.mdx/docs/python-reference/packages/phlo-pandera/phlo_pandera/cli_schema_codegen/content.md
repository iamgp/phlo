# cli_schema_codegen (/docs/python-reference/packages/phlo-pandera/phlo_pandera/cli_schema_codegen)



Schema code generation helpers and the `generate` CLI command.

Extracted from `cli_schema` to keep module size manageable.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_import_object&#x22;" type="&#x22;(ref) -> Any&#x22;">
      Import an object from a "module:attr" reference.

      <PySourceCode>
        ```python
        def _import_object(ref: str) -> Any:
            """Import an object from a "module:attr" reference.

            Args:
                ref: Reference string in format "module:attr" (e.g., "workflows.ingestion.github.user_events:user_events").

            Returns:
                The imported object.

            Raises:
                click.ClickException: If the reference format is invalid or object not found.

            """
            import importlib

            if ":" not in ref:
                raise click.ClickException(
                    "Invalid reference. Expected 'module:attr' "
                    "(e.g. workflows.ingestion.github.user_events:user_events)."
                )

            module_name, attr = ref.split(":", 1)
            module = importlib.import_module(module_name)
            try:
                return getattr(module, attr)
            except AttributeError as exc:
                logger.warning(
                    "schema_codegen_import_attr_missing",
                    module_name=module_name,
                    attribute=attr,
                )
                raise click.ClickException(f"Object not found: {ref}") from exc
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;ref&#x22;" type="&#x22;str&#x22;" value="undefined">
          Reference string in format "module:attr" (e.g., "workflows.ingestion.github.user\_events:user\_events").
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;typing.Any&#x22;">
        The imported object.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_extract_source_callable&#x22;" type="&#x22;(obj) -> tuple[Callable[..., Any], dict[str, Any]]&#x22;">
      Extract a callable and metadata from a @phlo\_ingestion decorated object.

      Given a callable created via @phlo\_ingestion, returns a source builder
      function and best-effort metadata (table\_name, unique\_key, group).

      <PySourceCode>
        ```python
        def _extract_source_callable(obj: Any) -> tuple[Callable[..., Any], dict[str, Any]]:
            """Extract a callable and metadata from a @phlo_ingestion decorated object.

            Given a callable created via @phlo_ingestion, returns a source builder
            function and best-effort metadata (table_name, unique_key, group).

            Args:
                obj: Callable object decorated with @phlo_ingestion.

            Returns:
                Tuple of (source_builder_callable, metadata_dict).

            Raises:
                click.ClickException: If object is not callable or has invalid signature.

            """
            import inspect

            if callable(obj):
                meta: dict[str, Any] = {}
                table_config = getattr(obj, "_phlo_table_config", None)
                if table_config is not None:
                    meta["table_name"] = getattr(table_config, "table_name", None)
                    meta["unique_key"] = getattr(table_config, "unique_key", None)
                    meta["group"] = getattr(table_config, "group_name", None)

                sig = inspect.signature(obj)
                if "partition_date" not in sig.parameters:
                    raise click.ClickException(
                        "Unsupported asset source function signature: expected (partition_date: str)."
                    )

                return obj, meta

            raise click.ClickException("Unsupported input. Provide a callable created via @phlo_ingestion.")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;obj&#x22;" type="&#x22;Any&#x22;" value="undefined">
          Callable object decorated with @phlo\_ingestion.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;tuple&#x22;">
        Tuple of (source\_builder\_callable, metadata\_dict).
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_to_pascal_case&#x22;" type="&#x22;(name) -> str&#x22;">
      Convert a string to PascalCase.

      <PySourceCode>
        ```python
        def _to_pascal_case(name: str) -> str:
            """Convert a string to PascalCase.

            Args:
                name: Input string, may contain underscores or hyphens.

            Returns:
                PascalCase version of the input string.

            """
            parts = [p for p in name.replace("-", "_").split("_") if p]
            return "".join(p[:1].upper() + p[1:] for p in parts)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Input string, may contain underscores or hyphens.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        PascalCase version of the input string.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_snake_case&#x22;" type="&#x22;(name) -> str&#x22;">
      Convert a string to snake\_case.

      <PySourceCode>
        ```python
        def _snake_case(name: str) -> str:
            """Convert a string to snake_case.

            Args:
                name: Input string, may be PascalCase or camelCase.

            Returns:
                snake_case version of the input string.

            """
            s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
            return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Input string, may be PascalCase or camelCase.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        snake\_case version of the input string.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_map_dlt_type&#x22;" type="&#x22;(dlt_type) -> tuple[str, str | None]&#x22;">
      Map DLT schema data\_type strings to Python type annotations.

      <PySourceCode>
        ```python
        def _map_dlt_type(dlt_type: str) -> tuple[str, str | None]:
            """Map DLT schema data_type strings to Python type annotations.

            Args:
                dlt_type: DLT data type string (e.g., "text", "bigint", "timestamp").

            Returns:
                Tuple of (annotation, import_stmt) where import_stmt is a full
                'from x import y' line or None if no import needed.

            """
            normalized = dlt_type.lower()
            if normalized in {"text", "varchar", "char", "uuid"}:
                return "str", None
            if normalized in {"bigint", "int", "integer", "smallint", "tinyint"}:
                return "int", None
            if normalized in {"double", "float", "real"}:
                return "float", None
            if normalized in {"decimal"}:
                return "Decimal", "from decimal import Decimal"
            if normalized in {"bool", "boolean"}:
                return "bool", None
            if normalized in {"date"}:
                return "date", "from datetime import date"
            if "timestamp" in normalized or normalized in {"datetime"}:
                return "datetime", "from datetime import datetime"
            if normalized in {"json"}:
                return "dict[str, Any]", "from typing import Any"
            if normalized in {"binary", "bytes"}:
                return "bytes", None
            return "str", None
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;dlt_type&#x22;" type="&#x22;str&#x22;" value="undefined">
          DLT data type string (e.g., "text", "bigint", "timestamp").
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Tuple of (annotation, import\_stmt) where import\_stmt is a full
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_render_schema_module&#x22;" type="&#x22;(*, domain, class_name, columns, unique_key) -> str&#x22;">
      Render a Pandera schema module as a Python string.

      <PySourceCode>
        ```python
        def _render_schema_module(
            *,
            domain: str,
            class_name: str,
            columns: list[dict[str, Any]],
            unique_key: str | None,
        ) -> str:
            """Render a Pandera schema module as a Python string.

            Args:
                domain: Domain name for the module docstring.
                class_name: Name of the schema class to generate.
                columns: List of column dictionaries with name, annotation, nullable.
                unique_key: Optional unique key column name for Field constraints.

            Returns:
                Python source code for the schema module.

            """
            imports: set[str] = {"from __future__ import annotations", "from pandera.pandas import Field"}
            imports.add("from phlo_pandera.schemas import PhloSchema")

            fields_lines: list[str] = []
            for col in columns:
                col_name = col["name"]
                annotation = col["annotation"]
                nullable = col["nullable"]

                field_args: list[str] = []
                if unique_key and col_name == unique_key:
                    field_args.append("unique=True")
                    field_args.append("nullable=False")
                elif nullable:
                    field_args.append("nullable=True")

                field = ""
                if field_args:
                    field = f" = Field({', '.join(field_args)})"

                fields_lines.append(f"    {col_name}: {annotation}{field}")

            module_doc = (
                f'"""Pandera schemas for {domain} domain.\n\nGenerated via `phlo schema generate`.\n"""'
            )
            body = "\n".join(fields_lines) if fields_lines else "    pass"

            import_lines = "\n".join(sorted(imports))
            return f"{module_doc}\n\n{import_lines}\n\n\nclass {class_name}(PhloSchema):\n{body}\n"
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;domain&#x22;" type="&#x22;str&#x22;" value="undefined">
          Domain name for the module docstring.
        </PyParameter>

        <PyParameter name="&#x22;class_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Name of the schema class to generate.
        </PyParameter>

        <PyParameter name="&#x22;columns&#x22;" type="&#x22;list[dict[str, Any]]&#x22;" value="undefined">
          List of column dictionaries with name, annotation, nullable.
        </PyParameter>

        <PyParameter name="&#x22;unique_key&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Optional unique key column name for Field constraints.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Python source code for the schema module.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_ensure_parent_dir&#x22;" type="&#x22;(path) -> None&#x22;">
      Ensure the parent directory exists, creating if necessary.

      <PySourceCode>
        ```python
        def _ensure_parent_dir(path: Path) -> None:
            """Ensure the parent directory exists, creating if necessary.

            Args:
                path: File path whose parent directory should exist.

            Returns:
                None.

            """
            path.parent.mkdir(parents=True, exist_ok=True)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;path&#x22;" type="&#x22;Path&#x22;" value="undefined">
          File path whose parent directory should exist.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;">
        None.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_update_or_insert_class&#x22;" type="&#x22;(content, class_name, class_block) -> str&#x22;">
      Update an existing class definition or insert a new one.

      <PySourceCode>
        ```python
        def _update_or_insert_class(content: str, class_name: str, class_block: str) -> str:
            """Update an existing class definition or insert a new one.

            Args:
                content: Existing module content.
                class_name: Name of the class to update or insert.
                class_block: New class definition as a string.

            Returns:
                Updated module content with the class replaced or added.

            """
            tree = ast.parse(content)
            for node in tree.body:
                if (
                    isinstance(node, ast.ClassDef)
                    and node.name == class_name
                    and node.lineno
                    and node.end_lineno
                ):
                    lines = content.splitlines(keepends=True)
                    start = node.lineno - 1
                    end = node.end_lineno
                    return "".join(lines[:start]) + class_block + "".join(lines[end:])

            if not content.endswith("\n"):
                content += "\n"
            if not content.endswith("\n\n"):
                content += "\n"
            return content + class_block
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;content&#x22;" type="&#x22;str&#x22;" value="undefined">
          Existing module content.
        </PyParameter>

        <PyParameter name="&#x22;class_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Name of the class to update or insert.
        </PyParameter>

        <PyParameter name="&#x22;class_block&#x22;" type="&#x22;str&#x22;" value="undefined">
          New class definition as a string.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Updated module content with the class replaced or added.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_class_block_only&#x22;" type="&#x22;(module_code, class_name) -> str&#x22;">
      Extract a single class definition from a module.

      <PySourceCode>
        ```python
        def _class_block_only(module_code: str, class_name: str) -> str:
            """Extract a single class definition from a module.

            Args:
                module_code: Python module source code.
                class_name: Name of the class to extract.

            Returns:
                Class definition as a string.

            Raises:
                ValueError: If the class is not found in the module.

            """
            tree = ast.parse(module_code)
            lines = module_code.splitlines(keepends=True)
            for node in tree.body:
                if (
                    isinstance(node, ast.ClassDef)
                    and node.name == class_name
                    and node.lineno
                    and node.end_lineno
                ):
                    return "".join(lines[node.lineno - 1 : node.end_lineno])
            raise ValueError(f"class not found in generated module: {class_name}")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;module_code&#x22;" type="&#x22;str&#x22;" value="undefined">
          Python module source code.
        </PyParameter>

        <PyParameter name="&#x22;class_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Name of the class to extract.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Class definition as a string.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_ensure_imports_in_module&#x22;" type="&#x22;(content, import_lines) -> str&#x22;">
      Ensure a set of import lines exists in the module content.

      Insert import lines after any module docstring while keeping valid
      Python import ordering (e.g., **future** imports first).

      <PySourceCode>
        ```python
        def _ensure_imports_in_module(content: str, import_lines: list[str]) -> str:
            """Ensure a set of import lines exists in the module content.

            Insert import lines after any module docstring while keeping valid
            Python import ordering (e.g., __future__ imports first).

            Args:
                content: Existing Python module content.
                import_lines: List of import lines to ensure exist.

            Returns:
                Updated module content with imports added if not present.

            """
            if not import_lines:
                return content

            try:
                tree = ast.parse(content)
            except SyntaxError:
                logger.warning("schema_codegen_existing_module_invalid_syntax")
                # Don't try to be clever if the file is already invalid.
                return "\n".join(import_lines) + "\n" + content

            insert_after = 0
            if (
                tree.body
                and isinstance(tree.body[0], ast.Expr)
                and isinstance(getattr(tree.body[0], "value", None), ast.Constant)
                and isinstance(tree.body[0].value.value, str)
                and getattr(tree.body[0], "end_lineno", None)
            ):
                insert_after = tree.body[0].end_lineno

            lines = content.splitlines()
            existing = set(lines)
            to_add = [line for line in import_lines if line not in existing]
            if not to_add:
                return content

            lines[insert_after:insert_after] = to_add + [""]
            return "\n".join(lines) + ("\n" if not content.endswith("\n") else "")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;content&#x22;" type="&#x22;str&#x22;" value="undefined">
          Existing Python module content.
        </PyParameter>

        <PyParameter name="&#x22;import_lines&#x22;" type="&#x22;list[str]&#x22;" value="undefined">
          List of import lines to ensure exist.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Updated module content with imports added if not present.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;generate&#x22;" type="&#x22;(from_ref, dry_run, domain, table_name, class_name, partition_date, max_records, out_path, update, overwrite)&#x22;">
      Generate Pandera schemas from a bounded DLT inference sample.

      This runs a small DLT sample locally (filesystem destination) to infer schema,
      then emits a PhloSchema-based DataFrameModel into your lakehouse code
      (default: workflows/schemas/).

      <PySourceCode>
        ```python
        @click.command("generate")
        @click.option(
            "--from",
            "from_ref",
            required=True,
            help="Python reference to a callable or @phlo_ingestion asset (module:attr).",
        )
        @click.option("--dry-run", is_flag=True, help="Print generated schema without writing files.")
        @click.option(
            "--domain",
            required=True,
            help="Domain name (used for default output path and module docstring).",
        )
        @click.option("--table", "table_name", default=None, help="DLT table/resource name to generate.")
        @click.option(
            "--class",
            "class_name",
            default=None,
            help="Schema class name (default: Raw<TableName>).",
        )
        @click.option(
            "--partition-date",
            default=None,
            help="Partition date passed to ingestion source builder (default: today).",
        )
        @click.option(
            "--max-records",
            type=int,
            default=200,
            show_default=True,
            help="Limit records extracted per DLT resource during schema inference.",
        )
        @click.option(
            "--out",
            "out_path",
            default=None,
            help="Output schema file path (default: workflows/schemas/<domain>.py).",
        )
        @click.option(
            "--update",
            is_flag=True,
            help="Update/insert the class into an existing schema module (non-destructive).",
        )
        @click.option(
            "--overwrite",
            is_flag=True,
            help="Overwrite the entire output module if it exists (destructive).",
        )
        def generate(
            from_ref: str,
            dry_run: bool,
            domain: str,
            table_name: str | None,
            class_name: str | None,
            partition_date: str | None,
            max_records: int,
            out_path: str | None,
            update: bool,
            overwrite: bool,
        ):
            """Generate Pandera schemas from a bounded DLT inference sample.

            This runs a small DLT sample locally (filesystem destination) to infer schema,
            then emits a PhloSchema-based DataFrameModel into your lakehouse code
            (default: workflows/schemas/).

            Args:
                from_ref: Python reference to a callable or @phlo_ingestion asset (module:attr).
                dry_run: If True, print generated schema without writing files.
                domain: Domain name for output path and module docstring.
                table_name: DLT table/resource name to generate (optional).
                class_name: Schema class name (default: Raw<TableName>).
                partition_date: Partition date passed to ingestion source (default: today).
                max_records: Limit records extracted per DLT resource during inference.
                out_path: Output schema file path (default: workflows/schemas/<domain>.py).
                update: If True, update/insert class into existing module (non-destructive).
                overwrite: If True, overwrite entire output module (destructive).

            Returns:
                None. Writes schema file or prints to stdout if dry_run.

            Raises:
                click.ClickException: On invalid input or conflicts (e.g., --update and --overwrite).

            """
            import datetime as _dt
            import itertools
            import tempfile

            import dlt
            from rich.console import Console

            console = Console()

            obj = _import_object(from_ref)
            source_fn, meta = _extract_source_callable(obj)

            partition_date_value = partition_date or _dt.date.today().isoformat()
            dlt_obj = source_fn(partition_date_value)

            try:
                from dlt.extract.resource import DltResource
                from dlt.extract.source import DltSource
            except Exception as exc:  # pragma: no cover
                logger.exception(
                    "schema_codegen_dlt_import_failed",
                    from_ref=from_ref,
                )
                raise click.ClickException(f"Failed to import DLT types: {exc}") from exc

            if isinstance(dlt_obj, DltSource):
                for r in dlt_obj.resources.values():
                    try:
                        r.add_limit(max_records)
                    except Exception:
                        continue
            elif isinstance(dlt_obj, DltResource):
                dlt_obj.add_limit(max_records)
            elif hasattr(dlt_obj, "__iter__"):
                dlt_obj = itertools.islice(dlt_obj, max_records)

            with tempfile.TemporaryDirectory(prefix="phlo-schema-generate-") as tmpdir:
                pipeline = dlt.pipeline(
                    pipeline_name=f"phlo_schema_generate_{_dt.datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    destination=dlt.destinations.filesystem(bucket_url=Path(tmpdir).as_uri()),
                    dataset_name=_snake_case(domain),
                    pipelines_dir=tmpdir,
                )

                run_kwargs: dict[str, Any] = {"loader_file_format": "parquet"}
                if not isinstance(dlt_obj, (DltSource, DltResource)):
                    run_kwargs["table_name"] = meta.get("table_name") or table_name or "data"

                pipeline.run(dlt_obj, **run_kwargs)

                schema = pipeline.default_schema
                candidate_tables = [
                    t
                    for t in schema.tables.keys()
                    if not t.startswith("_dlt_") and t not in {"_dlt_pipeline_state"}
                ]

                selected_table = table_name
                if selected_table is None:
                    if len(candidate_tables) == 1:
                        selected_table = candidate_tables[0]
                    else:
                        raise click.ClickException(
                            "Multiple DLT tables inferred. Re-run with --table <name>. "
                            f"Candidates: {', '.join(sorted(candidate_tables))}"
                        )

                if selected_table not in schema.tables:
                    raise click.ClickException(
                        f"Table not found in inferred schema: {selected_table}. "
                        f"Available: {', '.join(sorted(candidate_tables))}"
                    )

                table = schema.tables[selected_table]
                dlt_columns: dict[str, Any] = table.get("columns") or {}

            unique_key = meta.get("unique_key")
            inferred_columns: list[dict[str, Any]] = []
            imports: set[str] = set()
            for col_name, col in sorted(dlt_columns.items()):
                if col_name.startswith("_dlt_") or col_name.startswith("_phlo_"):
                    continue

                ann, imp = _map_dlt_type(str(col.get("data_type", "text")))
                if imp:
                    imports.add(imp)

                nullable = bool(col.get("nullable", True))
                if unique_key and col_name == unique_key:
                    nullable = False
                annotation = ann if not nullable else f"{ann} | None"

                inferred_columns.append(
                    {
                        "name": col_name,
                        "annotation": annotation,
                        "nullable": nullable,
                        "dlt_type": col.get("data_type"),
                    }
                )

            base_name = meta.get("table_name") or selected_table
            schema_class = class_name or f"Raw{_to_pascal_case(base_name)}"

            module_code = _render_schema_module(
                domain=domain,
                class_name=schema_class,
                columns=inferred_columns,
                unique_key=unique_key,
            )

            # Add extra imports if needed by annotations.
            if imports:
                lines = module_code.splitlines()
                insert_at = 0
                for idx, line in enumerate(lines):
                    if line.startswith("from __future__ import annotations"):
                        insert_at = idx + 1
                        break
                extra = sorted(imports)
                lines[insert_at:insert_at] = extra
                module_code = "\n".join(lines) + "\n"

            output_path = (
                Path(out_path) if out_path else (_DEFAULT_SCHEMA_OUT_DIR / f"{_snake_case(domain)}.py")
            )

            if dry_run:
                click.echo(module_code)
                return

            if overwrite and update:
                raise click.ClickException("Use only one of --update or --overwrite.")

            _ensure_parent_dir(output_path)
            if not output_path.exists():
                output_path.write_text(module_code)
                console.print(f"[green]Wrote[/green] {output_path}")
                return

            if overwrite:
                output_path.write_text(module_code)
                console.print(f"[green]Overwrote[/green] {output_path}")
                return

            if not update:
                raise click.ClickException(
                    f"Refusing to overwrite existing file: {output_path}. Use --update or --overwrite."
                )

            existing = output_path.read_text()
            class_block = _class_block_only(module_code, schema_class)

            required_imports = [
                "from __future__ import annotations",
                "from pandera.pandas import Field",
                "from phlo_pandera.schemas import PhloSchema",
            ]
            existing = _ensure_imports_in_module(existing, required_imports)

            updated = _update_or_insert_class(existing, schema_class, class_block)
            output_path.write_text(updated)
            console.print(f"[green]Updated[/green] {output_path}")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;from_ref&#x22;" type="&#x22;str&#x22;" value="undefined">
          Python reference to a callable or @phlo\_ingestion asset (module:attr).
        </PyParameter>

        <PyParameter name="&#x22;dry_run&#x22;" type="&#x22;bool&#x22;" value="undefined">
          If True, print generated schema without writing files.
        </PyParameter>

        <PyParameter name="&#x22;domain&#x22;" type="&#x22;str&#x22;" value="undefined">
          Domain name for output path and module docstring.
        </PyParameter>

        <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          DLT table/resource name to generate (optional).
        </PyParameter>

        <PyParameter name="&#x22;class_name&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Schema class name (default: Raw\<TableName>).
        </PyParameter>

        <PyParameter name="&#x22;partition_date&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Partition date passed to ingestion source (default: today).
        </PyParameter>

        <PyParameter name="&#x22;max_records&#x22;" type="&#x22;int&#x22;" value="undefined">
          Limit records extracted per DLT resource during inference.
        </PyParameter>

        <PyParameter name="&#x22;out_path&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Output schema file path (default: workflows/schemas/\<domain>.py).
        </PyParameter>

        <PyParameter name="&#x22;update&#x22;" type="&#x22;bool&#x22;" value="undefined">
          If True, update/insert class into existing module (non-destructive).
        </PyParameter>

        <PyParameter name="&#x22;overwrite&#x22;" type="&#x22;bool&#x22;" value="undefined">
          If True, overwrite entire output module (destructive).
        </PyParameter>
      </div>

      <PyFunctionReturn type="null">
        None. Writes schema file or prints to stdout if dry\_run.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
