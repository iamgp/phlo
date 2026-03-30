# config (/docs/python-reference/core/phlo/cli/config)



Configuration Management Commands

Commands for managing phlo.yaml infrastructure configuration.

<PyAttribute name="&#x22;console&#x22;" type="null" value="&#x22;Console()&#x22;" />

<PyAttribute name="&#x22;error_console&#x22;" type="null" value="&#x22;Console(stderr=True)&#x22;" />

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;config&#x22;" type="&#x22;()&#x22;">
      Manage infrastructure configuration.

      <PySourceCode>
        ```python
        @click.group()
        def config():
            """Manage infrastructure configuration."""
        ```
      </PySourceCode>

      <PyFunctionReturn type="null" />
    </PyFunction>

    <PyFunction name="&#x22;show&#x22;" type="&#x22;(format)&#x22;">
      Show the effective infrastructure configuration.

      
      Examples:
      phlo config show
      phlo config show --format json

      <PySourceCode>
        ```python
        @config.command("show")
        @click.option(
            "--format",
            type=click.Choice(["yaml", "json"]),
            default="yaml",
            help="Output format",
        )
        def show(format: str):
            """Show the effective infrastructure configuration.

            \b
            Examples:
              phlo config show
              phlo config show --format json
            """
            infra_config = load_infrastructure_config()
            logger.info("config_show_succeeded", output_format=format)

            if format == "yaml":
                config_dict = infra_config.model_dump(exclude_none=False)
                yaml_output = yaml.dump(
                    {"infrastructure": config_dict},
                    default_flow_style=False,
                    sort_keys=False,
                )
                syntax = Syntax(yaml_output, "yaml", theme="monokai", line_numbers=False)
                console.print("\n[bold]Effective Infrastructure Configuration:[/bold]\n")
                console.print(syntax)
            else:
                config_dict = infra_config.model_dump(exclude_none=False)
                console.print_json(data={"infrastructure": config_dict})
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;format&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="null" />
    </PyFunction>

    <PyFunction name="&#x22;validate&#x22;" type="&#x22;()&#x22;">
      Validate infrastructure configuration in phlo.yaml.

      
      Examples:
      phlo config validate

      <PySourceCode>
        ```python
        @config.command("validate")
        def validate():
            """Validate infrastructure configuration in phlo.yaml.

            \b
            Examples:
              phlo config validate
            """
            config_path = Path.cwd() / "phlo.yaml"

            if not config_path.exists():
                logger.warning("config_validate_file_missing", path=str(config_path))
                console.print("[yellow]Warning: No phlo.yaml found in current directory[/yellow]")
                console.print("Run [cyan]phlo services init[/cyan] to create infrastructure configuration")
                sys.exit(1)

            console.print(f"Validating: {config_path}\n")

            with config_path.open() as f:
                project_config = yaml.safe_load(f)

            if not project_config:
                logger.warning("config_validate_empty_file", path=str(config_path))
                error_console.print("[red]Error: phlo.yaml is empty[/red]")
                sys.exit(1)

            if "infrastructure" not in project_config:
                logger.info("config_validate_infrastructure_missing", path=str(config_path))
                console.print("[yellow]Warning: No infrastructure section in phlo.yaml[/yellow]")
                console.print(
                    "Using default configuration. Run [cyan]phlo config upgrade[/cyan] to add infrastructure section."
                )
                return

            try:
                infra_data = project_config["infrastructure"]
                infra_config = InfrastructureConfig(**infra_data)
            except ValidationError as e:
                logger.warning(
                    "config_validate_failed",
                    path=str(config_path),
                    error_count=len(e.errors()),
                )
                error_console.print("[red]Validation Error:[/red]\n")
                for error in e.errors():
                    loc = " -> ".join(str(x) for x in error["loc"])
                    error_console.print(f"  [red]•[/red] {loc}: {error['msg']}")
                error_console.print(
                    "\n[yellow]Fix these errors in phlo.yaml and run validate again.[/yellow]"
                )
                sys.exit(1)

            logger.info(
                "config_validate_succeeded",
                path=str(config_path),
                service_count=len(infra_config.services),
            )

            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("Check", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Details")

            table.add_row("Schema Validation", "✓ Valid", "All fields conform to schema")
            table.add_row(
                "Services Defined",
                "✓ Valid",
                f"{len(infra_config.services)} services configured",
            )
            table.add_row(
                "Naming Pattern",
                "✓ Valid",
                f"Pattern: {infra_config.container_naming_pattern}",
            )
            table.add_row(
                "Network Config",
                "✓ Valid",
                f"Driver: {infra_config.network.driver}",
            )

            console.print(table)
            console.print("\n[green]✓ Configuration is valid![/green]\n")
        ```
      </PySourceCode>

      <PyFunctionReturn type="null" />
    </PyFunction>

    <PyFunction name="&#x22;upgrade&#x22;" type="&#x22;(force)&#x22;">
      Add infrastructure section to existing phlo.yaml.

      
      Examples:
      phlo config upgrade
      phlo config upgrade --force

      <PySourceCode>
        ```python
        @config.command("upgrade")
        @click.option("--force", is_flag=True, help="Overwrite existing infrastructure section")
        def upgrade(force: bool):
            """Add infrastructure section to existing phlo.yaml.

            \b
            Examples:
              phlo config upgrade
              phlo config upgrade --force
            """
            config_path = Path.cwd() / "phlo.yaml"

            if not config_path.exists():
                logger.warning("config_upgrade_file_missing", path=str(config_path))
                error_console.print("[red]Error: No phlo.yaml found in current directory[/red]")
                error_console.print("Run [cyan]phlo services init[/cyan] to create a new project")
                sys.exit(1)

            with config_path.open() as f:
                project_config = yaml.safe_load(f) or {}

            if "infrastructure" in project_config and not force:
                logger.warning(
                    "config_upgrade_skipped", path=str(config_path), reason="infrastructure_exists"
                )
                console.print("[yellow]Infrastructure section already exists in phlo.yaml[/yellow]")
                error_console.print("Use --force to overwrite")
                sys.exit(1)

            default_infra = InfrastructureConfig()
            project_config["infrastructure"] = default_infra.model_dump(exclude_none=False, mode="python")

            with config_path.open("w") as f:
                yaml.dump(
                    project_config,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                )

            console.print(f"[green]✓ Updated {config_path}[/green]")
            console.print("Added infrastructure section\n")

            clear_config_cache()
            logger.info("config_upgrade_succeeded", path=str(config_path), force=force)

            console.print("Next steps:")
            console.print("  1. Review the infrastructure section in phlo.yaml")
            console.print("  2. Run [cyan]phlo config validate[/cyan] to verify")
            console.print("  3. Customize service names or container patterns if needed")
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;force&#x22;" type="&#x22;bool&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="null" />
    </PyFunction>
  </Tab>
</Tabs>
