# phlo_dagster (/docs/python-reference/packages/phlo-dagster/phlo_dagster)



Dagster orchestration adapter package for Phlo.

This package provides the Dagster-based orchestration layer for Phlo data pipelines.
It bridges Phlo's capability-based architecture with Dagster's asset-centric execution model.

Key Components:

* DagsterOrchestratorAdapter: Translates Phlo capability specs into Dagster definitions
* DagsterServicePlugin: Manages Dagster webserver and daemon services
* DagsterExtensionPlugin: Extensibility interface for custom Dagster plugins
* Framework definitions: Entry point for user workflow discovery

Integration Points:

* Translates AssetSpec objects into @asset decorated functions
* Converts AssetCheckSpec into Dagster asset checks
* Maps ResourceSpec to Dagster resources
* Supports partitioned assets (daily, etc.)
* Handles Dagster-specific configuration (freshness policies, automation conditions)

Example:
Basic usage within a Phlo project::

from phlo\_dagster import DagsterServicePlugin

Service plugin handles container orchestration [#service-plugin-handles-container-orchestration]

plugin = DagsterServicePlugin()

Framework definitions entry point::

In workspace.yaml [#in-workspaceyaml]

load\_from:

* python\_module:
  module\_name: phlo\_dagster.framework.definitions

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['DagsterServicePlugin', 'DagsterExtensionPlugin', 'IngestionEnginePlugin', 'DagsterSettings', 'get_settings']&#x22;" />

<PyAttribute name="&#x22;__version__&#x22;" type="null" value="&#x22;'0.2.3'&#x22;" />

<Tabs items="[&#x22;Modules&#x22;]">
  <Tab value="&#x22;Modules&#x22;">
    <Cards>
      <Card href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/maintenance_policy&#x22;" title="&#x22;maintenance_policy&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/cli_materialize&#x22;" title="&#x22;cli_materialize&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/plugin&#x22;" title="&#x22;plugin&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/wap_sensors&#x22;" title="&#x22;wap_sensors&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/alerting_sensor&#x22;" title="&#x22;alerting_sensor&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/cli_plugin&#x22;" title="&#x22;cli_plugin&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/cli_logs&#x22;" title="&#x22;cli_logs&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/observatory_plugin&#x22;" title="&#x22;observatory_plugin&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/cli_logs_display&#x22;" title="&#x22;cli_logs_display&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/logging&#x22;" title="&#x22;logging&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/settings&#x22;" title="&#x22;settings&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/partitions&#x22;" title="&#x22;partitions&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/adapter&#x22;" title="&#x22;adapter&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/iceberg_maintenance&#x22;" title="&#x22;iceberg_maintenance&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/dagster_ext&#x22;" title="&#x22;dagster_ext&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/cli_dev&#x22;" title="&#x22;cli_dev&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/maintenance_sensor&#x22;" title="&#x22;maintenance_sensor&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/containers&#x22;" title="&#x22;containers&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/iceberg_maintenance_utils&#x22;" title="&#x22;iceberg_maintenance_utils&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/cli_backfill&#x22;" title="&#x22;cli_backfill&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/cli_status&#x22;" title="&#x22;cli_status&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/framework&#x22;" title="&#x22;framework&#x22;" />
    </Cards>
  </Tab>
</Tabs>
