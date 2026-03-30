# containers (/docs/python-reference/packages/phlo-dagster/phlo_dagster/containers)



Docker container discovery for Dagster services.

This module provides utilities for finding and managing Dagster-related
Docker containers within a Docker Compose environment. It handles
candidate container name generation and resolution across different
naming conventions.

Naming Conventions:

* Legacy: \{project\_name}-dagster-webserver-1
* New: \{project\_name}-dagster-1
* Configured: From infrastructure settings

The module attempts resolution in order: configured → new → legacy,
falling back through available patterns until a running container is found.

Example:
Finding the Dagster container::

from phlo\_dagster.containers import find\_dagster\_container

container\_name = find\_dagster\_container("my\_project")

Returns: "my_project-dagster-1" or similar [#returns-my_project-dagster-1-or-similar]

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;DagsterContainerCandidates&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/containers/DagsterContainerCandidates&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;dagster_container_candidates&#x22;" type="&#x22;(project_name, configured_name) -> DagsterContainerCandidates&#x22;">
      Build candidate container names for a project.

      <PySourceCode>
        ```python
        def dagster_container_candidates(
            project_name: str, configured_name: str | None
        ) -> DagsterContainerCandidates:
            """Build candidate container names for a project.

            Args:
                project_name: Compose project name.
                configured_name: Optional configured container name override.

            Returns:
                Ordered candidate names for Dagster webserver discovery.

            """

            configured = configured_name or ""
            new = f"{project_name}-dagster-1"
            legacy = f"{project_name}-dagster-webserver-1"
            return DagsterContainerCandidates(configured=configured, new=new, legacy=legacy)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;project_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Compose project name.
        </PyParameter>

        <PyParameter name="&#x22;configured_name&#x22;" type="&#x22;str | None&#x22;" value="undefined">
          Optional configured container name override.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;phlo_dagster.containers.DagsterContainerCandidates&#x22;">
        Ordered candidate names for Dagster webserver discovery.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_resolve_container_name&#x22;" type="&#x22;(service_name, project_name) -> str&#x22;">
      Resolve container name for a service from infrastructure settings.

      <PySourceCode>
        ```python
        def _resolve_container_name(service_name: str, project_name: str) -> str:
            """Resolve container name for a service from infrastructure settings.

            Args:
                service_name: Service identifier in infrastructure config.
                project_name: Compose project name.

            Returns:
                Configured or derived container name for the service.

            """

            return resolve_container_name(service_name, project_name)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;service_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Service identifier in infrastructure config.
        </PyParameter>

        <PyParameter name="&#x22;project_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Compose project name.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Configured or derived container name for the service.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_list_running_containers&#x22;" type="&#x22;(project_name) -> list[str]&#x22;">
      List running compose container names for a project.

      <PySourceCode>
        ```python
        def _list_running_containers(project_name: str) -> list[str]:
            """List running compose container names for a project.

            Args:
                project_name: Compose project name.

            Returns:
                List of running container names.

            """
            return list_running_containers(project_name)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;project_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Compose project name.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        List of running container names.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;find_dagster_container&#x22;" type="&#x22;(project_name) -> str&#x22;">
      Find the running Dagster webserver container for a project.

      <PySourceCode>
        ```python
        def find_dagster_container(project_name: str) -> str:
            """Find the running Dagster webserver container for a project.

            Args:
                project_name: Compose project name.

            Returns:
                Selected Dagster container name.

            Raises:
                RuntimeError: If no matching Dagster webserver container is running.

            """

            logger.info(
                "dagster_container_lookup_started",
                project_name=project_name,
            )
            try:
                chosen = find_service_container(
                    project_name=project_name,
                    service_name="dagster",
                    legacy_names=(f"{project_name}-dagster-webserver-1",),
                    include_pattern=rf"{re.escape(project_name)}.*dagster",
                    exclude_substrings=("daemon",),
                )
                logger.info(
                    "dagster_container_lookup_completed",
                    project_name=project_name,
                    selected_container=chosen,
                )
                return chosen
            except Exception as exc:
                logger.error(
                    "dagster_container_lookup_failed",
                    project_name=project_name,
                    error=str(exc),
                    exc_info=True,
                )
                raise
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;project_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Compose project name.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Selected Dagster container name.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
