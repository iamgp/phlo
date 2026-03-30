# cli_workflow (/docs/python-reference/packages/phlo-dlt/phlo_dlt/cli_workflow)



Workflow management commands.

This module provides CLI commands for creating and managing DLT-based
workflows. It implements the `phlo workflow` command group with
subcommands for scaffolding new ingestion pipelines.

Command Groups:

* `workflow`: Main workflow management group
* `workflow create`: Create new ingestion workflow scaffold

Command Options:
\--type: Workflow type (currently only "ingestion")
\--domain: Domain name (e.g., weather, stripe)
\--table: Table name for the ingestion
\--unique-key: Field name for deduplication
\--cron: Cron schedule expression
\--api-base-url: REST API base URL (optional)
\--field: Additional schema fields (repeatable)

Generated Files:
For each workflow, creates three files:

1. `workflows/schemas/\{domain\}.py`: Pandera schema definition
2. `workflows/ingestion/\{domain\}/\{table\}.py`: Ingestion asset
3. `tests/test_\{domain\}_\{table\}.py`: Unit tests

See Also:

* :mod:`phlo_dlt.scaffold`: Scaffolding implementation
* :mod:`phlo_dlt.cli_plugin`: Plugin that exposes these commands
* Click documentation: [https://click.palletsprojects.com/](https://click.palletsprojects.com/)

Example:

```bash
# Create a new ingestion workflow
phlo workflow create --domain weather --table observations --unique-key id

# With additional fields
phlo workflow create         --domain weather         --table observations         --unique-key station_id         --field temperature:float         --field humidity:float         --field recorded_at:datetime
```

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;workflow_group&#x22;" type="&#x22;() -> None&#x22;">
      Manage workflows.

      Command group for workflow operations including creation,
      listing, and management of ingestion and transformation workflows.

      Subcommands:
      create: Create a new workflow scaffold

      Example:

      ```bash
      phlo workflow --help
      phlo workflow create --help
      ```

      <PySourceCode>
        ````python
        @click.group(name="workflow")
        def workflow_group() -> None:
            """Manage workflows.

            Command group for workflow operations including creation,
            listing, and management of ingestion and transformation workflows.

            Subcommands:
                create: Create a new workflow scaffold

            Example:
                \```bash
                phlo workflow --help
                phlo workflow create --help
                \```

            """
        ````
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;create_workflow_cmd&#x22;" type="&#x22;(workflow_type, domain, table, unique_key, cron, api_base_url, fields) -> None&#x22;">
      Create a workflow scaffold.

      Generates the initial file structure for a new DLT ingestion workflow:

      * Pandera schema in workflows/schemas/\{domain}.py
      * Ingestion asset in workflows/ingestion/\{domain}/\{table}.py
      * Unit tests in tests/test\_\{domain}\_\{table}.py

      <Callout title="&#x22;Exits&#x22;" type="&#x22;exits&#x22;">
        0: Success
        1: Error (unsupported type or exception)
      </Callout>

      <Callout title="&#x22;Example&#x22;" type="&#x22;example&#x22;">
        ```bash
        # Interactive mode (prompts for all values)
        phlo workflow create

        # Non-interactive with all options
        phlo workflow create             --type ingestion             --domain weather             --table observations             --unique-key station_id             --cron "0 */6 * * *"             --api-base-url "https://api.weather.com/v1"             --field temperature:float             --field humidity:float

        # Nullable and required fields
        phlo workflow create             --domain users             --table profiles             --unique-key user_id             --field middle_name:str?             --field email:str!
        ```
      </Callout>

      <PySourceCode>
        ````python
        @workflow_group.command("create")
        @click.option(
            "--type",
            "workflow_type",
            type=click.Choice(["ingestion"]),
            prompt="Workflow type",
            help="Type of workflow to create (ingestion only)",
        )
        @click.option("--domain", prompt="Domain name", help="Domain name (e.g., weather, stripe, github)")
        @click.option("--table", prompt="Table name", help="Table name for ingestion")
        @click.option(
            "--unique-key",
            prompt="Unique key field",
            help="Field name for deduplication (e.g., id, _id)",
        )
        @click.option(
            "--cron",
            default="0 */1 * * *",
            prompt="Cron schedule",
            help="Cron schedule expression",
        )
        @click.option(
            "--api-base-url",
            prompt="API base URL (optional)",
            default="",
            help="REST API base URL",
        )
        @click.option(
            "--field",
            "fields",
            multiple=True,
            help="Additional schema field (name:type, name:type?, name:type!)",
        )
        def create_workflow_cmd(
            workflow_type: str,
            domain: str,
            table: str,
            unique_key: str,
            cron: str,
            api_base_url: str,
            fields: tuple[str, ...],
        ) -> None:
            """Create a workflow scaffold.

            Generates the initial file structure for a new DLT ingestion workflow:
            - Pandera schema in workflows/schemas/{domain}.py
            - Ingestion asset in workflows/ingestion/{domain}/{table}.py
            - Unit tests in tests/test_{domain}_{table}.py

            Args:
                workflow_type: Type of workflow (currently only "ingestion" supported)
                domain: Domain/category name for the data (e.g., "weather", "stripe")
                table: Target table name
                unique_key: Column name to use for deduplication
                cron: Cron expression for scheduling (default: "0 */1 * * *")
                api_base_url: Base URL for REST API source (optional)
                fields: Additional schema fields as "name:type" strings

            Exits:
                0: Success
                1: Error (unsupported type or exception)

            Example:
                \```bash
                # Interactive mode (prompts for all values)
                phlo workflow create

                # Non-interactive with all options
                phlo workflow create \
                    --type ingestion \
                    --domain weather \
                    --table observations \
                    --unique-key station_id \
                    --cron "0 */6 * * *" \
                    --api-base-url "https://api.weather.com/v1" \
                    --field temperature:float \
                    --field humidity:float

                # Nullable and required fields
                phlo workflow create \
                    --domain users \
                    --table profiles \
                    --unique-key user_id \
                    --field middle_name:str? \
                    --field email:str!
                \```

            """
            from phlo_dlt.scaffold import create_ingestion_workflow

            logger.info(
                "dlt_workflow_create_started",
                workflow_type=workflow_type,
                domain=domain,
                table=table,
                field_count=len(fields),
            )
            click.echo(f"\nCreating {workflow_type} workflow for {domain}.{table}...\n")

            try:
                if workflow_type == "ingestion":
                    files = create_ingestion_workflow(
                        domain=domain,
                        table_name=table,
                        unique_key=unique_key,
                        cron=cron,
                        api_base_url=api_base_url or None,
                        fields=list(fields),
                    )

                    click.echo("Created files:\n")
                    for file_path in files:
                        click.echo(f"  - {file_path}")

                    click.echo("\nNext steps:")
                    click.echo(f"  1. Edit schema: {files[0]}")
                    click.echo(f"  2. Configure API: {files[1]}")
                    click.echo("  3. Restart Dagster: docker restart dagster-webserver")
                    click.echo(f"  4. Test: phlo test {domain}")
                    click.echo(f"  5. Materialize: phlo materialize dlt_{table}")
                    logger.info(
                        "dlt_workflow_create_succeeded",
                        workflow_type=workflow_type,
                        domain=domain,
                        table=table,
                        file_count=len(files),
                    )
                else:
                    logger.warning(
                        "dlt_workflow_create_unsupported_type",
                        workflow_type=workflow_type,
                    )
                    click.echo(f"Error: Workflow type '{workflow_type}' not yet implemented", err=True)
                    click.echo("Currently supported: ingestion", err=True)
                    sys.exit(1)
            except Exception as exc:
                logger.exception(
                    "dlt_workflow_create_failed",
                    workflow_type=workflow_type,
                    domain=domain,
                    table=table,
                )
                click.echo(f"Error creating workflow: {exc}", err=True)
                sys.exit(1)
        ````
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;workflow_type&#x22;" type="&#x22;str&#x22;" value="undefined">
          Type of workflow (currently only "ingestion" supported)
        </PyParameter>

        <PyParameter name="&#x22;domain&#x22;" type="&#x22;str&#x22;" value="undefined">
          Domain/category name for the data (e.g., "weather", "stripe")
        </PyParameter>

        <PyParameter name="&#x22;table&#x22;" type="&#x22;str&#x22;" value="undefined">
          Target table name
        </PyParameter>

        <PyParameter name="&#x22;unique_key&#x22;" type="&#x22;str&#x22;" value="undefined">
          Column name to use for deduplication
        </PyParameter>

        <PyParameter name="&#x22;cron&#x22;" type="&#x22;str&#x22;" value="undefined">
          Cron expression for scheduling (default: "0 \*/1 \* \* \*")
        </PyParameter>

        <PyParameter name="&#x22;api_base_url&#x22;" type="&#x22;str&#x22;" value="undefined">
          Base URL for REST API source (optional)
        </PyParameter>

        <PyParameter name="&#x22;fields&#x22;" type="&#x22;tuple[str, ...]&#x22;" value="undefined">
          Additional schema fields as "name:type" strings
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
