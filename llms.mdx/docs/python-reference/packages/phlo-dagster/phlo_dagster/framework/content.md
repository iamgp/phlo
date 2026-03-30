# framework (/docs/python-reference/packages/phlo-dagster/phlo_dagster/framework)



Dagster framework helpers for Phlo projects.

This module provides the main entry point for Dagster-based Phlo projects.
It exports the core definitions building functionality that discovers and
loads user workflows from the configured workflows directory.

Exported Components:

* build\_definitions: Function to build merged Dagster definitions from
  user workflows and framework resources
* defs: Global Definitions instance for Dagster to load

Architecture:
The framework module serves as the bridge between Phlo's capability-based
plugin system and Dagster's execution model. It handles:

* Workflow discovery from user project directories
* Resource injection and configuration
* WAP (Write-Audit-Publish) sensor registration
* Executor selection based on platform

Usage:
In workspace.yaml::

load\_from:

* python\_module:
  module\_name: phlo\_dagster.framework.definitions

Or programmatically::

from phlo\_dagster.framework import build\_definitions

defs = build\_definitions(workflows\_path="custom\_workflows")

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['build_definitions', 'defs']&#x22;" />

<Tabs items="[&#x22;Modules&#x22;]">
  <Tab value="&#x22;Modules&#x22;">
    <Cards>
      <Card href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/framework/definitions&#x22;" title="&#x22;definitions&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/framework/schema_contracts&#x22;" title="&#x22;schema_contracts&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/framework/discovery&#x22;" title="&#x22;discovery&#x22;" />
    </Cards>
  </Tab>
</Tabs>
