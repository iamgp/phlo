# cli_plugin (/docs/python-reference/packages/phlo-dagster/phlo_dagster/cli_plugin)



CLI plugin for Dagster-related commands.

This module registers the Dagster CLI command group with Phlo's plugin
system. It exposes commands for workflow management, log access, status
monitoring, and asset materialization.

Commands Provided:

* dev: Start Dagster development server
* logs: Access and filter Dagster run logs
* status: Show asset and service health status
* backfill: Run partitioned materializations in batch
* materialize: Materialize assets via Docker

Plugin Registration:
The DagsterCliPlugin implements CliCommandPlugin and is auto-discovered
via entry\_points (group: phlo.plugins.cli\_commands).

Command Organization:
Commands follow the lifecycle:

* Development: dev
* Monitoring: logs, status
* Execution: materialize, backfill

Integration:
Commands integrate with Docker containers for execution, ensuring
consistent environment and resource access.

Example:
CLI usage::

phlo dev                    # Start dev server
phlo logs --follow          # Tail logs
phlo status --services      # Check service health
phlo materialize dlt\_orders # Materialize asset
phlo backfill dlt\_orders --start-date 2024-01-01 --end-date 2024-01-31

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;DagsterCliPlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/cli_plugin/DagsterCliPlugin&#x22;" />
    </Cards>
  </Tab>
</Tabs>
