# cli_plugin (/docs/python-reference/packages/phlo-dlt/phlo_dlt/cli_plugin)



CLI plugin for DLT workflow scaffolding.

This module provides the DltCliPlugin class that exposes DLT-specific
CLI commands to the Phlo command-line interface. It integrates the
workflow scaffolding commands into the Phlo CLI.

Key Class:

* :class:`DltCliPlugin`: CLI command plugin for DLT workflows

Commands Exposed:

* `phlo workflow create`: Create new ingestion workflow scaffold

Plugin Registration:
This plugin is discovered via entry points defined in pyproject.toml:

* `phlo.cli_commands`: DltCliPlugin

See Also:

* :mod:`phlo.plugins.base`: Base plugin interfaces
* :mod:`phlo_dlt.cli_workflow`: Workflow command implementation
* :mod:`phlo_dlt.scaffold`: Scaffolding logic

Example:
The plugin is auto-discovered by Phlo:

```bash
# User runs through Phlo CLI
phlo workflow create --domain weather --table observations
```

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;DltCliPlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dlt/phlo_dlt/cli_plugin/DltCliPlugin&#x22;" />
    </Cards>
  </Tab>
</Tabs>
