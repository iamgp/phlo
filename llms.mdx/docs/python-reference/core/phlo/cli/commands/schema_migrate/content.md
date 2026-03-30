# schema_migrate (/docs/python-reference/core/phlo/cli/commands/schema_migrate)



Schema migration CLI commands.

Provides commands to diff, plan, apply, and inspect schema migrations
between quality provider schemas and storage tables.

<PyAttribute name="&#x22;console&#x22;" type="null" value="&#x22;Console()&#x22;" />

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_resolve_migrator&#x22;" type="&#x22;() -> Any&#x22;">
      Resolve the registered SchemaMigrator from the capability registry.

      <PySourceCode>
        ```python
        def _resolve_migrator() -> Any:
            """Resolve the registered SchemaMigrator from the capability registry."""
            from phlo.capabilities.discovery import discover_capabilities

            discover_capabilities()

            registry = get_capability_registry()
            migrators = registry.list_schema_migrators()
            if not migrators:
                console.print("[red]No schema migrator registered.[/red]")
                console.print(
                    "Install a storage provider (e.g. phlo-iceberg) that implements SchemaMigrator."
                )
                sys.exit(1)

            migrators_by_name = {migrator.name: migrator for migrator in migrators}

            configured_migrator = configured_capability_name("schema_migrator")
            if configured_migrator:
                selected = migrators_by_name.get(configured_migrator)
                if selected is None:
                    available = list_capabilities("schema_migrator")
                    console.print(
                        f"[red]Configured schema migrator '{configured_migrator}' is not registered.[/red]"
                    )
                    console.print(f"Available schema migrators: {available}")
                    sys.exit(1)
                return selected.provider

            default_table_store = configured_capability_name("table_store")
            if default_table_store:
                selected = migrators_by_name.get(default_table_store)
                if selected is not None:
                    return selected.provider

            if len(migrators) == 1:
                return migrators[0].provider

            available = list_capabilities("schema_migrator")
            table_store_options = list_capabilities("table_store")
            console.print("[red]Multiple schema migrators are registered and none was selected.[/red]")
            console.print("Configure `schema_migrator` directly or set a matching default `table_store`.")
            if default_table_store:
                console.print(
                    f"[yellow]Configured table_store '{default_table_store}' does not match any "
                    "registered schema migrator.[/yellow]"
                )
            console.print(f"Available schema migrators: {available}")
            if table_store_options:
                console.print(f"Available table stores: {table_store_options}")
            sys.exit(1)
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;typing.Any&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_resolve_extractor&#x22;" type="&#x22;() -> Any&#x22;">
      Resolve a SchemaExtractor by attempting known quality providers.

      <PySourceCode>
        ```python
        def _resolve_extractor() -> Any:
            """Resolve a SchemaExtractor by attempting known quality providers."""
            try:
                from phlo_pandera.schema_extractor import PanderaSchemaExtractor

                return PanderaSchemaExtractor()
            except ImportError:
                return None
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;typing.Any&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_discover_schema_for_table&#x22;" type="&#x22;(table_name) -> Any&#x22;">
      Discover the quality provider schema associated with a table name.

      Searches discovered Pandera schemas for a class whose metadata or naming
      convention matches the table.

      <PySourceCode>
        ```python
        def _discover_schema_for_table(table_name: str) -> Any:
            """Discover the quality provider schema associated with a table name.

            Searches discovered Pandera schemas for a class whose metadata or naming
            convention matches the table.
            """
            schemas: dict[str, Any] = {}
            try:
                from phlo_pandera.cli_schema_utils import discover_pandera_schemas

                schemas = discover_pandera_schemas()
            except ImportError:
                # Continue with file-based fallback discovery.
                pass

            short_name = table_name.split(".")[-1] if "." in table_name else table_name

            for name, schema_cls in schemas.items():
                cls_lower = name.lower().replace("_", "")
                table_lower = short_name.lower().replace("_", "")
                if cls_lower == table_lower or table_lower in cls_lower:
                    return schema_cls

            fallback_schemas = _discover_pandera_schemas_from_files()
            for name, schema_cls in fallback_schemas.items():
                cls_lower = name.lower().replace("_", "")
                table_lower = short_name.lower().replace("_", "")
                if cls_lower == table_lower or table_lower in cls_lower:
                    return schema_cls
            return None
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;typing.Any&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_discover_pandera_schemas_from_files&#x22;" type="&#x22;() -> dict[str, type[Any]]&#x22;">
      Fallback schema discovery that loads files directly to avoid import-path collisions.

      <PySourceCode>
        ```python
        def _discover_pandera_schemas_from_files() -> dict[str, type[Any]]:
            """Fallback schema discovery that loads files directly to avoid import-path collisions."""
            try:
                from pandera.pandas import DataFrameModel
            except ImportError:
                return {}

            env_paths = os.getenv("PHLO_SCHEMA_SEARCH_PATHS")
            if env_paths:
                search_paths = [Path(path.strip()) for path in env_paths.split(",") if path.strip()]
            else:
                project_root = os.getenv("PHLO_PROJECT_PATH")
                if project_root:
                    root = Path(project_root)
                    search_paths = [root / "examples", root / "workflows"]
                else:
                    search_paths = [Path("examples"), Path("workflows")]

            discovered: dict[str, type[Any]] = {}
            for root in search_paths:
                if not root.exists():
                    continue
                for schema_file in root.glob("**/schemas/*.py"):
                    if schema_file.name.startswith("_"):
                        continue
                    module_name = f"phlo_schema_fallback_{abs(hash(schema_file.resolve()))}"
                    spec = importlib.util.spec_from_file_location(module_name, schema_file)
                    if spec is None or spec.loader is None:
                        continue
                    module = importlib.util.module_from_spec(spec)
                    try:
                        spec.loader.exec_module(module)
                    except Exception:
                        continue

                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, DataFrameModel) and obj is not DataFrameModel:
                            discovered[name] = obj
            return discovered
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;dict[str, type[typing.Any]]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_resolve_desired_schema&#x22;" type="&#x22;(table_name, schema_class) -> tuple[Any, Any, Any]&#x22;">
      Resolve migrator, extracted desired schema, and native schema class.

      <PySourceCode>
        ```python
        def _resolve_desired_schema(table_name: str, schema_class: str | None) -> tuple[Any, Any, Any]:
            """Resolve migrator, extracted desired schema, and native schema class."""
            migrator = _resolve_migrator()
            extractor = _resolve_extractor()

            native_schema = _find_native_schema(table_name, schema_class)
            if native_schema is None:
                console.print(f"[red]No quality schema found for table: {table_name}[/red]")
                sys.exit(1)

            if extractor is None:
                console.print("[red]No schema extractor available. Install phlo-pandera.[/red]")
                sys.exit(1)

            desired = extractor.extract(native_schema)
            return migrator, desired, native_schema
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;schema_class&#x22;" type="&#x22;str | None&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;tuple[typing.Any, typing.Any, typing.Any]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_select_default_table_store_name&#x22;" type="&#x22;() -> str | None&#x22;">
      Return the selected default table-store name, if available.

      <PySourceCode>
        ```python
        def _select_default_table_store_name() -> str | None:
            """Return the selected default table-store name, if available."""
            resolution = resolve_capability("table_store")
            return resolution.name if resolution is not None else None
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;str | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_select_default_migrator_name&#x22;" type="&#x22;() -> str | None&#x22;">
      Return the selected default schema-migrator name, if available.

      <PySourceCode>
        ```python
        def _select_default_migrator_name() -> str | None:
            """Return the selected default schema-migrator name, if available."""
            resolution = resolve_capability("schema_migrator")
            return resolution.name if resolution is not None else None
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;str | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_collect_quality_checks&#x22;" type="&#x22;(table_name) -> list[dict[str, Any]]&#x22;">
      Collect registered check metadata associated with a table asset.

      <PySourceCode>
        ```python
        def _collect_quality_checks(table_name: str) -> list[dict[str, Any]]:
            """Collect registered check metadata associated with a table asset."""
            short_name = table_name.split(".")[-1]
            target_key = f"dlt_{short_name}"
            checks: list[dict[str, Any]] = []
            for check in get_capability_registry().list_checks():
                if check.asset_key != target_key:
                    continue
                tags = dict(check.tags)
                consumers = tags.get("contract_consumers", "")
                contract_consumers = [c for c in consumers.split(",") if c]
                contract_sla: dict[str, Any] | None = None
                raw_sla = tags.get("contract_sla")
                if raw_sla:
                    try:
                        parsed = json.loads(raw_sla)
                        if isinstance(parsed, dict):
                            contract_sla = parsed
                    except json.JSONDecodeError:
                        contract_sla = None
                checks.append(
                    {
                        "name": check.name,
                        "severity": check.severity,
                        "blocking": check.blocking,
                        "description": check.description,
                        "tags": tags,
                        "owner": tags.get("contract_owner"),
                        "consumers": contract_consumers,
                        "sla": contract_sla,
                    }
                )
            return checks
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;list[dict[str, typing.Any]]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_collect_contract_metadata&#x22;" type="&#x22;(table_name) -> dict[str, Any]&#x22;">
      Collect owner/consumer/SLA metadata for a table contract.

      <PySourceCode>
        ```python
        def _collect_contract_metadata(table_name: str) -> dict[str, Any]:
            """Collect owner/consumer/SLA metadata for a table contract."""
            short_name = table_name.split(".")[-1]
            target_key = f"dlt_{short_name}"
            owner: str | None = None
            consumers: list[dict[str, Any]] = []
            sla: dict[str, Any] | None = None

            for asset in get_capability_registry().list_assets():
                if asset.key != target_key:
                    continue
                if asset.metadata.get("table_name") not in {short_name, table_name}:
                    continue

                asset_owner = asset.metadata.get("owner")
                if isinstance(asset_owner, str) and asset_owner:
                    owner = asset_owner

                asset_consumers = asset.metadata.get("consumers")
                if isinstance(asset_consumers, list):
                    consumers = [c for c in asset_consumers if isinstance(c, dict)]

                asset_sla = asset.metadata.get("sla")
                if isinstance(asset_sla, dict):
                    sla = asset_sla
                break

            return {"owner": owner, "consumers": consumers, "sla": sla}
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_collect_transform_refs&#x22;" type="&#x22;(table_name) -> list[str]&#x22;">
      Collect transform asset refs that likely depend on the table.

      <PySourceCode>
        ```python
        def _collect_transform_refs(table_name: str) -> list[str]:
            """Collect transform asset refs that likely depend on the table."""
            short_name = table_name.split(".")[-1]
            target_key = f"dlt_{short_name}"
            refs: list[str] = []
            for asset in get_capability_registry().list_assets():
                kinds = asset.kinds or set()
                deps = asset.deps or []
                if "dbt" not in kinds:
                    continue
                if target_key in deps or short_name in deps:
                    refs.append(asset.key)
            return sorted(set(refs))
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;list[str]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;export_contract_for_table&#x22;" type="&#x22;(*, table_name, schema_class=None, output_path=None, force=False) -> Path&#x22;">
      Export a schema contract for a table and return output path.

      <PySourceCode>
        ```python
        def export_contract_for_table(
            *,
            table_name: str,
            schema_class: str | None = None,
            output_path: Path | None = None,
            force: bool = False,
        ) -> Path:
            """Export a schema contract for a table and return output path."""
            migrator, desired, native_schema = _resolve_desired_schema(table_name, schema_class)
            migration_plan = migrator.diff_schema(table_name=table_name, desired=desired)
            now = datetime.now(UTC).isoformat()

            contract = {
                "contract_version": schema_migrate_contracts.CONTRACT_VERSION,
                "generated_at": now,
                "table_name": table_name,
                "schema_class": getattr(native_schema, "__name__", None),
                "table_store": _select_default_table_store_name(),
                "schema_migrator": _select_default_migrator_name(),
                "normalized_schema": asdict(desired),
                "migration_plan": asdict(migration_plan),
                "contract_metadata": _collect_contract_metadata(table_name),
                "quality_checks": _collect_quality_checks(table_name),
                "transform_refs": _collect_transform_refs(table_name),
            }
            destination = output_path or schema_migrate_contracts.default_contract_path(table_name)
            schema_migrate_contracts.write_contract(destination, contract, force=force)
            return destination
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;schema_class&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

        <PyParameter name="&#x22;output_path&#x22;" type="&#x22;Path | None&#x22;" value="&#x22;None&#x22;" />

        <PyParameter name="&#x22;force&#x22;" type="&#x22;bool&#x22;" value="&#x22;False&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;pathlib.Path&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;refresh_contracts_for_selection&#x22;" type="&#x22;(*, selection=None, force=True) -> int&#x22;">
      Refresh contracts for a materialization selection. Returns write count.

      <PySourceCode>
        ```python
        def refresh_contracts_for_selection(
            *,
            selection: str | None = None,
            force: bool = True,
        ) -> int:
            """Refresh contracts for a materialization selection. Returns write count."""
            registry = get_capability_registry()
            candidate_tables: set[str] = set()
            selection_value = (selection or "").strip()

            if selection_value.startswith("dlt_"):
                candidate_tables.add(selection_value.removeprefix("dlt_"))

            for asset in registry.list_assets():
                kinds = asset.kinds or set()
                if "dlt" not in kinds:
                    continue
                table_name = asset.metadata.get("table_name")
                if not isinstance(table_name, str) or not table_name:
                    continue
                if selection_value and selection_value.startswith("dlt_") and asset.key != selection_value:
                    continue
                candidate_tables.add(table_name)

            refreshed_count = 0
            for table in sorted(candidate_tables):
                table_candidates = [table]
                if "." not in table:
                    try:
                        from phlo_dlt.settings import get_settings

                        namespace = get_settings().dlt_default_namespace
                        table_candidates.insert(0, f"{namespace}.{table}")
                    except Exception:
                        pass

                for candidate in table_candidates:
                    try:
                        export_contract_for_table(table_name=candidate, force=force)
                    except SystemExit:
                        continue
                    except Exception:
                        logger.warning(
                            "schema_contract_refresh_failed",
                            table_name=candidate,
                            selection=selection_value or None,
                            exc_info=True,
                        )
                        continue
                    refreshed_count += 1
                    break
            return refreshed_count
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;selection&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

        <PyParameter name="&#x22;force&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;int&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;schema_migrate_group&#x22;" type="&#x22;() -> None&#x22;">
      Schema migration between quality schemas and storage tables.

      <PySourceCode>
        ```python
        @click.group("schema-migrate")
        def schema_migrate_group() -> None:
            """Schema migration between quality schemas and storage tables."""
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;diff&#x22;" type="&#x22;(table_name, schema_class, fmt) -> None&#x22;">
      Show pending schema changes between quality schema and storage table.

      <PySourceCode>
        ```python
        @schema_migrate_group.command()
        @click.argument("table_name")
        @click.option(
            "--schema-class", default=None, help="Pandera schema class name (auto-detected if omitted)"
        )
        @click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
        def diff(table_name: str, schema_class: str | None, fmt: str) -> None:
            """Show pending schema changes between quality schema and storage table.

            Examples:
                phlo schema-migrate diff warehouse.customers
                phlo schema-migrate diff warehouse.customers --schema-class CustomerSchema
                phlo schema-migrate diff warehouse.customers --format json
            """
            migrator, desired, _ = _resolve_desired_schema(table_name, schema_class)
            plan = migrator.diff_schema(table_name=table_name, desired=desired)

            if fmt == "json":
                click.echo(json.dumps(asdict(plan), indent=2))
                return

            if not plan.changes:
                console.print(f"[green]No schema changes detected for {table_name}[/green]")
                return

            _render_plan(plan)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;schema_class&#x22;" type="&#x22;str | None&#x22;" value="null" />

        <PyParameter name="&#x22;fmt&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;plan&#x22;" type="&#x22;(table_name, schema_class, fmt) -> None&#x22;">
      Generate a migration plan for a table.

      <PySourceCode>
        ```python
        @schema_migrate_group.command()
        @click.argument("table_name")
        @click.option(
            "--schema-class", default=None, help="Pandera schema class name (auto-detected if omitted)"
        )
        @click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
        def plan(table_name: str, schema_class: str | None, fmt: str) -> None:
            """Generate a migration plan for a table.

            Examples:
                phlo schema-migrate plan warehouse.customers
            """
            migrator, desired, _ = _resolve_desired_schema(table_name, schema_class)
            migration_plan = migrator.diff_schema(table_name=table_name, desired=desired)

            if fmt == "json":
                click.echo(json.dumps(asdict(migration_plan), indent=2))
                return

            if not migration_plan.changes:
                console.print(f"[green]No migration needed for {table_name}[/green]")
                return

            _render_plan(migration_plan)

            if migration_plan.recommendations:
                console.print("\n[bold]Recommendations:[/bold]")
                for rec in migration_plan.recommendations:
                    console.print(f"  • {rec}")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;schema_class&#x22;" type="&#x22;str | None&#x22;" value="null" />

        <PyParameter name="&#x22;fmt&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;apply&#x22;" type="&#x22;(table_name, schema_class, yes, dry_run) -> None&#x22;">
      Apply schema migration to a storage table.

      Safe changes are applied automatically. Breaking changes require
      confirmation (or --yes to skip the prompt).

      <PySourceCode>
        ```python
        @schema_migrate_group.command()
        @click.argument("table_name")
        @click.option(
            "--schema-class", default=None, help="Pandera schema class name (auto-detected if omitted)"
        )
        @click.option("--yes", is_flag=True, help="Auto-approve breaking changes")
        @click.option("--dry-run", is_flag=True, help="Show what would be applied without executing")
        def apply(table_name: str, schema_class: str | None, yes: bool, dry_run: bool) -> None:
            """Apply schema migration to a storage table.

            Safe changes are applied automatically. Breaking changes require
            confirmation (or --yes to skip the prompt).

            Examples:
                phlo schema-migrate apply warehouse.customers
                phlo schema-migrate apply warehouse.customers --yes
                phlo schema-migrate apply warehouse.customers --dry-run
            """
            migrator, desired, _ = _resolve_desired_schema(table_name, schema_class)
            migration_plan = migrator.diff_schema(table_name=table_name, desired=desired)

            if not migration_plan.changes:
                console.print(f"[green]No migration needed for {table_name}[/green]")
                return

            _render_plan(migration_plan)

            if dry_run:
                console.print("\n[yellow]Dry run — no changes applied.[/yellow]")
                return

            approved = not migration_plan.requires_approval
            if migration_plan.requires_approval:
                if yes:
                    approved = True
                else:
                    console.print(
                        f"\n[yellow]This plan contains breaking changes "
                        f"(classification: {migration_plan.classification}).[/yellow]"
                    )
                    approved = click.confirm("Apply breaking changes?", default=False)

            if not approved:
                console.print("[yellow]Migration cancelled.[/yellow]")
                return

            try:
                result = migrator.apply_plan(plan=migration_plan, approved=approved)
                console.print("\n[green]Migration applied successfully.[/green]")
                for key, value in result.items():
                    console.print(f"  {key}: {value}")
            except Exception as exc:
                logger.exception("schema_migrate_apply_failed", table_name=table_name)
                console.print(f"[red]Migration failed: {exc}[/red]")
                sys.exit(1)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;schema_class&#x22;" type="&#x22;str | None&#x22;" value="null" />

        <PyParameter name="&#x22;yes&#x22;" type="&#x22;bool&#x22;" value="null" />

        <PyParameter name="&#x22;dry_run&#x22;" type="&#x22;bool&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;history&#x22;" type="&#x22;(table_name, limit, fmt) -> None&#x22;">
      Show schema version history for a table.

      <PySourceCode>
        ```python
        @schema_migrate_group.command()
        @click.argument("table_name")
        @click.option("--limit", default=10, help="Max history entries to show")
        @click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
        def history(table_name: str, limit: int, fmt: str) -> None:
            """Show schema version history for a table.

            Examples:
                phlo schema-migrate history warehouse.customers
                phlo schema-migrate history warehouse.customers --limit 5
                phlo schema-migrate history warehouse.customers --format json
            """
            migrator = _resolve_migrator()

            entries = migrator.get_schema_history(table_name=table_name, limit=limit)

            if fmt == "json":
                click.echo(json.dumps(entries, indent=2, default=str))
                return

            if not entries:
                console.print(f"[yellow]No schema history found for {table_name}[/yellow]")
                return

            table = Table(title=f"Schema History: {table_name}")
            table.add_column("Snapshot", style="cyan")
            table.add_column("Timestamp", style="green")
            table.add_column("Summary", style="dim")

            for entry in entries:
                timestamp = entry.get("timestamp")
                if timestamp is None:
                    timestamp = entry.get("timestamp_ms", "")
                table.add_row(
                    str(entry.get("snapshot_id", "")),
                    str(timestamp),
                    str(entry.get("summary", "")),
                )

            console.print(table)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;limit&#x22;" type="&#x22;int&#x22;" value="null" />

        <PyParameter name="&#x22;fmt&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;export_contract&#x22;" type="&#x22;(table_name, schema_class, output_path, force) -> None&#x22;">
      Export a Phlo contract snapshot for a table.

      <PySourceCode>
        ```python
        @schema_migrate_group.command("export-contract")
        @click.argument("table_name")
        @click.option(
            "--schema-class", default=None, help="Pandera schema class name (auto-detected if omitted)"
        )
        @click.option(
            "--output",
            "output_path",
            type=click.Path(path_type=Path, dir_okay=False),
            default=None,
            help="Contract output path (default: .phlo/contracts/<table>.json)",
        )
        @click.option("--force", is_flag=True, help="Overwrite existing output file")
        def export_contract(
            table_name: str,
            schema_class: str | None,
            output_path: Path | None,
            force: bool,
        ) -> None:
            """Export a Phlo contract snapshot for a table."""
            try:
                destination = export_contract_for_table(
                    table_name=table_name,
                    schema_class=schema_class,
                    output_path=output_path,
                    force=force,
                )
            except FileExistsError as exc:
                console.print(f"[red]{exc}[/red]")
                sys.exit(1)

            console.print(f"[green]Exported contract:[/green] {destination}")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;schema_class&#x22;" type="&#x22;str | None&#x22;" value="null" />

        <PyParameter name="&#x22;output_path&#x22;" type="&#x22;Path | None&#x22;" value="null" />

        <PyParameter name="&#x22;force&#x22;" type="&#x22;bool&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;scaffold_yaml&#x22;" type="&#x22;(table_name, contract_path, output_path, force) -> None&#x22;">
      Generate migration scaffold YAML from a Phlo contract.

      <PySourceCode>
        ```python
        @schema_migrate_group.command("scaffold-yaml")
        @click.argument("table_name")
        @click.option(
            "--from-contract",
            "contract_path",
            type=click.Path(path_type=Path, dir_okay=False),
            default=None,
            help="Path to contract JSON (default: .phlo/contracts/<table>.json)",
        )
        @click.option(
            "--output",
            "output_path",
            type=click.Path(path_type=Path, dir_okay=False),
            default=None,
            help="YAML output path (default: .phlo/migrations/<table>.yaml)",
        )
        @click.option("--force", is_flag=True, help="Overwrite existing output file")
        def scaffold_yaml(
            table_name: str,
            contract_path: Path | None,
            output_path: Path | None,
            force: bool,
        ) -> None:
            """Generate migration scaffold YAML from a Phlo contract."""
            source_path = contract_path or schema_migrate_contracts.default_contract_path(table_name)
            destination = output_path or schema_migrate_contracts.default_scaffold_yaml_path(table_name)

            try:
                payload = _build_scaffold_payload_from_contract(
                    table_name=table_name,
                    contract_path=source_path,
                )
                schema_migrate_contracts.write_scaffold_yaml(
                    destination,
                    payload=payload,
                    force=force,
                )
            except (FileNotFoundError, ValueError, json.JSONDecodeError, TypeError, FileExistsError) as exc:
                console.print(f"[red]{exc}[/red]")
                sys.exit(1)

            console.print(f"[green]Generated migration scaffold:[/green] {destination}")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;contract_path&#x22;" type="&#x22;Path | None&#x22;" value="null" />

        <PyParameter name="&#x22;output_path&#x22;" type="&#x22;Path | None&#x22;" value="null" />

        <PyParameter name="&#x22;force&#x22;" type="&#x22;bool&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;scaffold_yaml_recent&#x22;" type="&#x22;(since_hours, limit, force) -> None&#x22;">
      Generate migration scaffold YAML files for recent .phlo/contracts additions.

      <PySourceCode>
        ```python
        @schema_migrate_group.command("scaffold-yaml-recent")
        @click.option(
            "--since-hours",
            type=int,
            default=24,
            show_default=True,
            help="Only include contracts modified in the last N hours",
        )
        @click.option(
            "--limit",
            type=int,
            default=None,
            help="Maximum number of contract additions to scaffold",
        )
        @click.option("--force", is_flag=True, help="Overwrite existing output files")
        def scaffold_yaml_recent(since_hours: int, limit: int | None, force: bool) -> None:
            """Generate migration scaffold YAML files for recent .phlo/contracts additions."""
            if since_hours < 0:
                console.print("[red]--since-hours must be >= 0[/red]")
                sys.exit(1)
            if limit is not None and limit <= 0:
                console.print("[red]--limit must be > 0[/red]")
                sys.exit(1)

            contract_paths = schema_migrate_contracts.list_recent_contract_paths(
                since_hours=since_hours,
                limit=limit,
            )
            if not contract_paths:
                console.print("[yellow]No recent contracts found in .phlo/contracts[/yellow]")
                return

            generated_count = 0
            errors: list[str] = []
            for contract_path in contract_paths:
                try:
                    contract = schema_migrate_contracts.read_contract(contract_path)
                    table_name = contract.get("table_name")
                    if not isinstance(table_name, str) or not table_name:
                        raise ValueError(f"Contract missing table_name: {contract_path}")

                    payload = _build_scaffold_payload_from_contract(
                        table_name=table_name,
                        contract_path=contract_path,
                    )
                    destination = schema_migrate_contracts.default_scaffold_yaml_path(table_name)
                    schema_migrate_contracts.write_scaffold_yaml(destination, payload=payload, force=force)
                    generated_count += 1
                    console.print(
                        f"[green]Generated migration scaffold:[/green] {destination} (from {contract_path})"
                    )
                except (
                    FileNotFoundError,
                    ValueError,
                    json.JSONDecodeError,
                    TypeError,
                    FileExistsError,
                ) as exc:
                    message = f"{contract_path}: {exc}"
                    errors.append(message)
                    console.print(f"[yellow]Skipping contract due to error:[/yellow] {message}")

            console.print(f"[green]Generated {generated_count} migration scaffolds.[/green]")
            if errors:
                console.print(
                    f"[red]Encountered {len(errors)} errors while scaffolding recent contracts.[/red]"
                )
                for error in errors:
                    console.print(f"- {error}")
                sys.exit(1)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;since_hours&#x22;" type="&#x22;int&#x22;" value="null" />

        <PyParameter name="&#x22;limit&#x22;" type="&#x22;int | None&#x22;" value="null" />

        <PyParameter name="&#x22;force&#x22;" type="&#x22;bool&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_build_scaffold_payload_from_contract&#x22;" type="&#x22;(*, table_name, contract_path) -> dict[str, Any]&#x22;">
      <PySourceCode>
        ```python
        def _build_scaffold_payload_from_contract(
            *, table_name: str, contract_path: Path
        ) -> dict[str, Any]:
            contract = schema_migrate_contracts.read_contract(contract_path)
            contract_table = contract.get("table_name")
            if contract_table != table_name:
                raise ValueError(
                    f"Contract table mismatch: expected '{table_name}', found '{contract_table}'"
                )

            desired_payload = contract.get("normalized_schema")
            if not isinstance(desired_payload, dict):
                raise ValueError("Contract missing normalized_schema payload")

            fields_payload = desired_payload.get("fields", [])
            metadata_payload = desired_payload.get("metadata", {})
            if not isinstance(fields_payload, list) or not isinstance(metadata_payload, dict):
                raise ValueError("Invalid normalized_schema payload in contract")

            desired = NormalizedSchema(
                fields=[FieldSpec(**field_data) for field_data in fields_payload],
                metadata=metadata_payload,
            )
            migrator = _resolve_migrator()
            migration_plan = migrator.diff_schema(table_name=table_name, desired=desired)

            return schema_migrate_contracts.build_scaffold_payload(
                table_name=table_name,
                contract=contract,
                migration_plan=migration_plan,
                generated_at=datetime.now(UTC).isoformat(),
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;contract_path&#x22;" type="&#x22;Path&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;dict[str, typing.Any]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_find_native_schema&#x22;" type="&#x22;(table_name, schema_class) -> Any&#x22;">
      Find the native quality schema for a table.

      <PySourceCode>
        ```python
        def _find_native_schema(table_name: str, schema_class: str | None) -> Any:
            """Find the native quality schema for a table."""
            if schema_class:
                candidates: dict[str, Any] = {}
                try:
                    from phlo_pandera.cli_schema_utils import discover_pandera_schemas

                    candidates.update(discover_pandera_schemas())
                except ImportError:
                    pass
                # Keep primary discovery authoritative; fallback only fills missing names.
                for name, schema in _discover_pandera_schemas_from_files().items():
                    candidates.setdefault(name, schema)

                if schema_class in candidates:
                    return candidates[schema_class]

                # Support module-qualified references (e.g. workflows.schemas.demo.RawSchema)
                short_name = schema_class.split(".")[-1]
                if short_name in candidates:
                    return candidates[short_name]

                console.print(f"[red]Schema class not found: {schema_class}[/red]")
                return None

            return _discover_schema_for_table(table_name)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;schema_class&#x22;" type="&#x22;str | None&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;typing.Any&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_render_plan&#x22;" type="&#x22;(plan) -> None&#x22;">
      Render a SchemaMigrationPlan as a rich table.

      <PySourceCode>
        ```python
        def _render_plan(plan: Any) -> None:
            """Render a SchemaMigrationPlan as a rich table."""
            classification_colors = {
                "safe": "green",
                "warning": "yellow",
                "breaking": "red",
            }
            color = classification_colors.get(plan.classification, "white")

            console.print(f"\n[bold]Migration Plan: {plan.table_name}[/bold]")
            console.print(f"Classification: [{color}]{plan.classification}[/{color}]")
            console.print(f"Requires approval: {'Yes' if plan.requires_approval else 'No'}\n")

            table = Table()
            table.add_column("Field", style="cyan")
            table.add_column("Change", style="magenta")
            table.add_column("Old", style="dim")
            table.add_column("New", style="dim")
            table.add_column("Classification")

            for change in plan.changes:
                c_color = classification_colors.get(change.classification, "white")
                table.add_row(
                    change.field_name,
                    change.change_type,
                    change.old_value or "",
                    change.new_value or "",
                    f"[{c_color}]{change.classification}[/{c_color}]",
                )

            console.print(table)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;plan&#x22;" type="&#x22;Any&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
