# workflow (/docs/python-reference/core/phlo/cli/commands/workflow)



Workflow management commands.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;workflow_group&#x22;" type="&#x22;() -> None&#x22;">
      Manage workflows.

      <PySourceCode>
        ```python
        @click.group(name="workflow")
        def workflow_group() -> None:
            """Manage workflows."""
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;create_workflow_cmd&#x22;" type="&#x22;(workflow_type, domain, table, unique_key, cron, api_base_url, fields) -> None&#x22;">
      Create a workflow scaffold.

      <PySourceCode>
        ```python
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
            """Create a workflow scaffold."""
            from phlo_dlt.scaffold import create_ingestion_workflow

            logger.info(
                "workflow_create_started",
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
                    click.echo("  3. Restart Dagster: phlo services restart dagster")
                    click.echo(f"  4. Test: phlo test {domain}")
                    click.echo(f"  5. Materialize: phlo materialize dlt_{table}")
                    logger.info(
                        "workflow_create_succeeded",
                        workflow_type=workflow_type,
                        domain=domain,
                        table=table,
                        file_count=len(files),
                    )
            except Exception as exc:
                logger.exception(
                    "workflow_create_failed",
                    workflow_type=workflow_type,
                    domain=domain,
                    table=table,
                )
                click.echo(f"Error creating workflow: {exc}", err=True)
                sys.exit(1)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;workflow_type&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;domain&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;table&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;unique_key&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;cron&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;api_base_url&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;fields&#x22;" type="&#x22;tuple[str, ...]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
