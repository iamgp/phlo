# containers (/docs/python-reference/core/phlo/infrastructure/containers)



Core helpers for resolving running service containers.

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;resolve_container_name&#x22;" type="&#x22;(service_name, project_name) -> str&#x22;">
      Resolve container name for a service from infrastructure settings.

      <PySourceCode>
        ```python
        def resolve_container_name(service_name: str, project_name: str) -> str:
            """Resolve container name for a service from infrastructure settings."""
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

    <PyFunction name="&#x22;list_running_containers&#x22;" type="&#x22;(project_name) -> list[str]&#x22;">
      List running compose container names for a project.

      <PySourceCode>
        ```python
        def list_running_containers(project_name: str) -> list[str]:
            """List running compose container names for a project."""
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    f"label=com.docker.compose.project={project_name}",
                    "--format",
                    "{{.Names}}",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            return result.stdout.splitlines() if result.stdout else []
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;project_name&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;list[str]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;select_first_existing&#x22;" type="&#x22;(candidates, existing) -> str | None&#x22;">
      Return the first candidate present in the existing container list.

      <PySourceCode>
        ```python
        def select_first_existing(candidates: Iterable[str], existing: Iterable[str]) -> str | None:
            """Return the first candidate present in the existing container list."""
            existing_set = set(existing)
            for candidate in candidates:
                if candidate and candidate in existing_set:
                    return candidate
            return None
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;candidates&#x22;" type="&#x22;Iterable[str]&#x22;" value="null" />

        <PyParameter name="&#x22;existing&#x22;" type="&#x22;Iterable[str]&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;str | None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;find_service_container&#x22;" type="&#x22;(*, project_name, service_name, legacy_names=(), include_pattern=None, exclude_substrings=()) -> str&#x22;">
      Find a running service container for a compose project.

      <PySourceCode>
        ```python
        def find_service_container(
            *,
            project_name: str,
            service_name: str,
            legacy_names: Iterable[str] = (),
            include_pattern: str | None = None,
            exclude_substrings: Iterable[str] = (),
        ) -> str:
            """Find a running service container for a compose project."""
            configured_name = resolve_container_name(service_name, project_name)
            default_name = f"{project_name}-{service_name}-1"
            preferred = [configured_name, default_name, *legacy_names]

            existing = list_running_containers(project_name)
            chosen = select_first_existing(preferred, existing)
            if chosen:
                return chosen

            pattern = include_pattern or rf"{re.escape(project_name)}.*{re.escape(service_name)}"
            for name in existing:
                if not re.search(pattern, name):
                    continue
                if any(excluded in name for excluded in exclude_substrings):
                    continue
                return name

            legacy_list = [name for name in legacy_names if name]
            expected = [default_name, *legacy_list]
            expected_rendered = " or ".join(expected) if expected else default_name
            raise RuntimeError(
                f"Could not find running {service_name} container for project '{project_name}'. "
                f"Expected container name: {expected_rendered}"
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;project_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;service_name&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;legacy_names&#x22;" type="&#x22;Iterable[str]&#x22;" value="&#x22;()&#x22;" />

        <PyParameter name="&#x22;include_pattern&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;" />

        <PyParameter name="&#x22;exclude_substrings&#x22;" type="&#x22;Iterable[str]&#x22;" value="&#x22;()&#x22;" />
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
