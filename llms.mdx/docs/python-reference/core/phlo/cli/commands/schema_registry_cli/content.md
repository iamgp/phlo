# schema_registry_cli (/docs/python-reference/core/phlo/cli/commands/schema_registry_cli)



Schema registry CLI commands.

<PyAttribute name="&#x22;console&#x22;" type="null" value="&#x22;Console()&#x22;" />

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_require_registry_db_url&#x22;" type="&#x22;() -> str&#x22;">
      Resolve and validate schema registry database URL.

      <PySourceCode>
        ```python
        def _require_registry_db_url() -> str:
            """Resolve and validate schema registry database URL."""
            db_url = resolve_registry_db_url()
            if db_url:
                return db_url

            console.print("[red]No registry database URL configured.[/red]")
            console.print(
                "Set PHLO_REGISTRY_DB_URL, PHLO_LINEAGE_DB_URL, or DAGSTER_PG_DB_CONNECTION_STRING."
            )
            raise SystemExit(1)
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;contracts&#x22;" type="&#x22;() -> None&#x22;">
      Schema registry and data contract management.

      <PySourceCode>
        ```python
        @click.group("contracts")
        def contracts() -> None:
            """Schema registry and data contract management."""
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;snapshot&#x22;" type="&#x22;(table, schema_file, run_id, source) -> None&#x22;">
      Snapshot a schema from a JSON file into the registry.

      <PySourceCode>
        ```python
        @contracts.command("snapshot")
        @click.option("--table", required=True, help="Fully-qualified table name")
        @click.option(
            "--schema-file",
            required=True,
            type=click.Path(exists=True, dir_okay=False),
            help="Path to canonical schema JSON file",
        )
        @click.option("--run-id", default=None, help="Pipeline run ID")
        @click.option("--source", default="cli", help="Snapshot source label")
        def snapshot(table: str, schema_file: str, run_id: str | None, source: str) -> None:
            """Snapshot a schema from a JSON file into the registry."""
            db_url = _require_registry_db_url()

            with Path(schema_file).open() as f:
                schema = deserialize_schema(f.read())

            registry = SchemaRegistry(db_url)
            snapshot_id = registry.snapshot_schema(table, schema, run_id=run_id, source=source)
            console.print(f"[green]Snapshot:[/green] {snapshot_id}")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;schema_file&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;run_id&#x22;" type="&#x22;str | None&#x22;" value="null" />

        <PyParameter name="&#x22;source&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;check&#x22;" type="&#x22;(table, fail_on) -> None&#x22;">
      Check schema compatibility for a table against its previous snapshot.

      <PySourceCode>
        ```python
        @contracts.command("check")
        @click.option("--table", required=True, help="Fully-qualified table name")
        @click.option(
            "--fail-on",
            type=click.Choice(["breaking", "warning"]),
            default="breaking",
            help="Exit non-zero when worst classification meets or exceeds this level",
        )
        def check(table: str, fail_on: str) -> None:
            """Check schema compatibility for a table against its previous snapshot."""
            db_url = _require_registry_db_url()

            registry = SchemaRegistry(db_url)
            snapshots = registry.get_latest_snapshots(table, limit=2)

            if len(snapshots) < 2:
                console.print(f"[yellow]Fewer than 2 snapshots for {table}; nothing to compare.[/yellow]")
                return

            current = deserialize_schema(snapshots[0].schema_json)
            previous = deserialize_schema(snapshots[1].schema_json)
            plan = check_compatibility(previous, current, table_name=table)

            classification_colors = {"safe": "green", "warning": "yellow", "breaking": "red"}
            color = classification_colors.get(plan.classification, "white")

            console.print(f"\n[bold]Compatibility Check: {plan.table_name}[/bold]")
            console.print(f"Classification: [{color}]{plan.classification}[/{color}]")
            console.print(f"Requires approval: {'Yes' if plan.requires_approval else 'No'}\n")

            if plan.changes:
                tbl = Table()
                tbl.add_column("Field", style="cyan")
                tbl.add_column("Change", style="magenta")
                tbl.add_column("Old", style="dim")
                tbl.add_column("New", style="dim")
                tbl.add_column("Classification")

                for change in plan.changes:
                    c_color = classification_colors.get(change.classification, "white")
                    tbl.add_row(
                        change.field_name,
                        change.change_type,
                        change.old_value or "",
                        change.new_value or "",
                        f"[{c_color}]{change.classification}[/{c_color}]",
                    )
                console.print(tbl)
            else:
                console.print("[green]No changes detected.[/green]")

            fail_on_idx = CLASSIFICATION_ORDER.index(fail_on)
            actual_idx = CLASSIFICATION_ORDER.index(plan.classification)
            if actual_idx >= fail_on_idx:
                sys.exit(1)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;table&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;fail_on&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
