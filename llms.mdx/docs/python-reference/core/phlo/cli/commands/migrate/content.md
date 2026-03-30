# migrate (/docs/python-reference/core/phlo/cli/commands/migrate)



Data migration CLI commands.

<PyAttribute name="&#x22;console&#x22;" type="null" value="&#x22;Console()&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;migrate_group&#x22;" type="&#x22;() -> None&#x22;">
      Data migration commands.

      <PySourceCode>
        ```python
        @click.group("migrate")
        def migrate_group() -> None:
            """Data migration commands."""
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;validate&#x22;" type="&#x22;(spec_file) -> None&#x22;">
      Validate a migration spec without executing.

      <PySourceCode>
        ```python
        @migrate_group.command("validate")
        @click.argument("spec_file", type=click.Path(path_type=Path, dir_okay=False))
        def validate(spec_file: Path) -> None:
            """Validate a migration spec without executing."""
            try:
                spec = load_migration_spec(spec_file)
            except MigrationSpecError as exc:
                console.print(f"[red]{exc}[/red]")
                sys.exit(1)

            executor = MigrationExecutor()
            errors = executor.validate(spec, dry_run_override=True)
            if errors:
                console.print("[red]Validation failed:[/red]")
                for error in errors:
                    console.print(f"- {error}")
                sys.exit(1)

            console.print(f"[green]Migration spec is valid:[/green] {spec_file}")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;spec_file&#x22;" type="&#x22;Path&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;run&#x22;" type="&#x22;(spec_file, dry_run, fmt) -> None&#x22;">
      Execute a migration spec.

      <PySourceCode>
        ```python
        @migrate_group.command("run")
        @click.argument("spec_file", type=click.Path(path_type=Path, dir_okay=False))
        @click.option("--dry-run", is_flag=True, help="Validate and read without writing")
        @click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
        def run(spec_file: Path, dry_run: bool, fmt: str) -> None:
            """Execute a migration spec."""
            try:
                spec = load_migration_spec(spec_file)
                result = MigrationExecutor().execute(
                    spec,
                    dry_run_override=True if dry_run else None,
                )
            except (MigrationSpecError, MigrationExecutionError) as exc:
                console.print(f"[red]{exc}[/red]")
                sys.exit(1)

            if fmt == "json":
                click.echo(json.dumps(asdict(result), indent=2, default=str))
                return

            console.print(f"[green]Migration {result.status}:[/green] {result.name}")
            console.print(f"Rows read: {result.rows_read}")
            console.print(f"Rows written: {result.rows_written}")
            console.print(f"Chunks processed: {result.chunks_processed}")
            console.print(f"Duration: {result.duration_seconds:.2f}s")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;spec_file&#x22;" type="&#x22;Path&#x22;" value="null" />

        <PyParameter name="&#x22;dry_run&#x22;" type="&#x22;bool&#x22;" value="null" />

        <PyParameter name="&#x22;fmt&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;list_specs&#x22;" type="&#x22;(directory) -> None&#x22;">
      List available migration spec files.

      <PySourceCode>
        ```python
        @migrate_group.command("list")
        @click.option(
            "--directory",
            "directory",
            type=click.Path(path_type=Path, file_okay=False),
            default=None,
            help="Directory to scan (defaults: migrations/, workflows/migrations/)",
        )
        def list_specs(directory: Path | None) -> None:
            """List available migration spec files."""
            candidates = [directory] if directory else [Path("migrations"), Path("workflows/migrations")]
            files: list[Path] = []

            for root in candidates:
                if root is None or not root.exists():
                    continue
                files.extend(sorted(root.glob("*.yaml")))
                files.extend(sorted(root.glob("*.yml")))

            deduped = sorted(set(files))
            if not deduped:
                console.print("[yellow]No migration specs found.[/yellow]")
                return

            for path in deduped:
                click.echo(str(path))
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;directory&#x22;" type="&#x22;Path | None&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;status&#x22;" type="&#x22;(limit, fmt) -> None&#x22;">
      Show recent migration history.

      <PySourceCode>
        ```python
        @migrate_group.command("status")
        @click.option("--limit", default=10, help="Max history entries to show")
        @click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table")
        def status(limit: int, fmt: str) -> None:
            """Show recent migration history."""
            entries = read_migration_history(limit=limit)
            if fmt == "json":
                click.echo(json.dumps(entries, indent=2, default=str))
                return

            if not entries:
                console.print("[yellow]No migration history found.[/yellow]")
                return

            table = Table(title="Recent Data Migrations")
            table.add_column("Name", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Rows Read", justify="right")
            table.add_column("Rows Written", justify="right")
            table.add_column("Chunks", justify="right")
            table.add_column("Timestamp", style="dim")

            for entry in entries:
                raw_metadata = entry.get("metadata")
                metadata: dict[str, object]
                metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
                table.add_row(
                    str(entry.get("name", "")),
                    str(entry.get("status", "")),
                    str(entry.get("rows_read", 0)),
                    str(entry.get("rows_written", 0)),
                    str(entry.get("chunks_processed", 0)),
                    str(metadata.get("timestamp", "")),
                )

            console.print(table)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;limit&#x22;" type="&#x22;int&#x22;" value="null" />

        <PyParameter name="&#x22;fmt&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
