# utils (/docs/python-reference/core/phlo/cli/infrastructure/utils)



Utility functions for CLI services that can be safely imported by plugins.

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;parse_env_file&#x22;" type="&#x22;(path) -> dict[str, str]&#x22;">
      Parse a .env file into a dict of key=value pairs.

      <PySourceCode>
        ```python
        def parse_env_file(path: Path) -> dict[str, str]:
            """Parse a .env file into a dict of key=value pairs."""
            if not path.exists():
                return {}
            values: dict[str, str] = {}
            try:
                for line in path.read_text().splitlines():
                    trimmed = line.strip()
                    if not trimmed or trimmed.startswith("#") or "=" not in trimmed:
                        continue
                    key, value = trimmed.split("=", 1)
                    values[key] = value
            except OSError:
                logger.warning("env_file_read_failed", path=str(path), exc_info=True)
                return {}
            return values
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;path&#x22;" type="&#x22;Path&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;dict[str, str]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;get_project_config&#x22;" type="&#x22;() -> dict&#x22;">
      Load phlo.yaml configuration.

      <PySourceCode>
        ```python
        def get_project_config() -> dict:
            """Load phlo.yaml configuration."""
            config_path = Path.cwd() / "phlo.yaml"
            if config_path.exists():
                try:
                    with config_path.open() as f:
                        config = yaml.safe_load(f) or {}
                        if isinstance(config, Mapping):
                            return dict(config)
                        logger.warning("project_config_invalid_type", path=str(config_path))
                except (OSError, yaml.YAMLError):
                    logger.warning("project_config_load_failed", path=str(config_path), exc_info=True)

            fallback_name = Path.cwd().name.lower().replace(" ", "-").replace("_", "-")
            logger.debug("project_config_fallback_used", project_name=fallback_name)
            return {
                "name": fallback_name,
                "description": "Phlo data lakehouse",
            }
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;dict&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;get_project_name&#x22;" type="&#x22;() -> str&#x22;">
      Get the project name for Docker Compose.

      <PySourceCode>
        ```python
        def get_project_name() -> str:
            """Get the project name for Docker Compose."""
            config = get_project_config()
            return config.get("name", Path.cwd().name.lower().replace(" ", "-").replace("_", "-"))
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_resolve_container_name&#x22;" type="&#x22;(service_name, project_name) -> str&#x22;">
      Resolve a service's container name using infra config or default pattern.

      <PySourceCode>
        ```python
        def _resolve_container_name(service_name: str, project_name: str) -> str:
            """Resolve a service's container name using infra config or default pattern."""
            from phlo.infrastructure import load_infrastructure_config

            infra = load_infrastructure_config()
            configured = infra.get_container_name(service_name, project_name)
            if configured:
                return configured
            return infra.container_naming_pattern.format(project=project_name, service=service_name)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;service_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;project_name&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
