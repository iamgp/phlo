# cli_plugin (/docs/python-reference/packages/phlo-lineage/phlo_lineage/cli_plugin)



CLI plugin for lineage commands.

This module provides the LineageCliPlugin class, which registers the lineage
CLI command group with the Phlo plugin system. It exposes all lineage-related
commands (show, export, impact, status, column) through the main phlo CLI.

Commands Exposed:

* lineage show: Display ASCII tree lineage visualization
* lineage export: Export to DOT, Mermaid, or JSON formats
* lineage impact: Analyze downstream impact of changes
* lineage status: Display graph statistics
* lineage column import-dbt: Import column lineage from dbt manifests
* lineage column upstream/downstream: Query column-level lineage

Plugin Registration:
This plugin is auto-discovered via the phlo.cli\_commands entry point.
No manual registration required.

Command Structure:
phlo lineage
├── show          # Visualize asset dependencies
├── export        # Export to external formats
├── impact        # Analyze change impact
├── status        # Graph statistics
└── column
├── import-dbt  # Import from dbt manifest
├── upstream    # Query upstream columns
└── downstream  # Query downstream columns

Example:
After plugin registration, commands are available via:

$ phlo lineage show orders
$ phlo lineage export orders --format dot --output lineage.dot
$ phlo lineage impact silver.stg\_orders
$ phlo lineage status

See Also:
phlo\_lineage.cli\_lineage for command implementations.
phlo.plugins.base.CliCommandPlugin for the plugin interface.

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;LineageCliPlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-lineage/phlo_lineage/cli_plugin/LineageCliPlugin&#x22;" />
    </Cards>
  </Tab>
</Tabs>
