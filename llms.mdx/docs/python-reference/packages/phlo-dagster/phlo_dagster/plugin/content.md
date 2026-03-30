# plugin (/docs/python-reference/packages/phlo-dagster/phlo_dagster/plugin)



Dagster service plugins for Phlo infrastructure management.

This module provides ServicePlugin implementations that register Dagster
services with Phlo's infrastructure management system. It handles service
definition loading from YAML files and provides metadata for the
Dagster webserver and daemon components.

Service Components:

* DagsterServicePlugin: Main webserver service
* DagsterDaemonServicePlugin: Background scheduler/sensor daemon

Service Definitions:
Services are defined in YAML files (service.yaml, dagster-daemon.yaml)
that specify Docker Compose configuration, ports, dependencies, and
startup behavior. These files are loaded from the package resources.

Plugin Registration:
Plugins are auto-discovered via entry\_points (group: phlo.plugins.services)
and contribute service definitions to the infrastructure orchestrator.

Service Responsibilities:

* Dagster Webserver: Serves UI, handles GraphQL queries, executes runs
* Dagster Daemon: Runs schedules, sensors, and daemon loops

Example:
Service definition structure (service.yaml)::

service:
name: dagster
description: Data orchestration platform
ports:

* "3000:3000"
  depends\_on:
* postgres
* trino

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;DagsterServicePlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/plugin/DagsterServicePlugin&#x22;" />

      <Card title="&#x22;DagsterDaemonServicePlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/plugin/DagsterDaemonServicePlugin&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_load_service_definition&#x22;" type="&#x22;(plugin_name, filename) -> dict[str, Any]&#x22;">
      Load a service definition YAML file from the phlo\_dagster package.

      <PySourceCode>
        ```python
        def _load_service_definition(plugin_name: str, filename: str) -> dict[str, Any]:
            """Load a service definition YAML file from the phlo_dagster package.

            Args:
                plugin_name: Logical name for logging (e.g. "dagster", "dagster_daemon").
                filename: YAML filename inside the phlo_dagster package.

            Returns:
                Parsed service configuration dict.

            Raises:
                Exception: If file cannot be read or parsed.

            """
            service_path = resources.files("phlo_dagster").joinpath(filename)
            logger.info(
                "dagster_service_definition_load_started",
                plugin_name=plugin_name,
                service_definition_path=str(service_path),
            )
            try:
                definition = yaml.safe_load(service_path.read_text(encoding="utf-8"))
                logger.info(
                    "dagster_service_definition_load_completed",
                    plugin_name=plugin_name,
                    service_definition_path=str(service_path),
                )
                return definition
            except Exception as exc:
                logger.error(
                    "dagster_service_definition_load_failed",
                    plugin_name=plugin_name,
                    service_definition_path=str(service_path),
                    error=str(exc),
                    exc_info=True,
                )
                raise
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;plugin_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Logical name for logging (e.g. "dagster", "dagster\_daemon").
        </PyParameter>

        <PyParameter name="&#x22;filename&#x22;" type="&#x22;str&#x22;" value="undefined">
          YAML filename inside the phlo\_dagster package.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict&#x22;">
        Parsed service configuration dict.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
