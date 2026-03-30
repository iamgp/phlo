# compose (/docs/python-reference/core/phlo/cli/infrastructure/compose)



<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;compose_base_cmd&#x22;" type="&#x22;(*, phlo_dir, project_name, profiles=()) -> list[str]&#x22;">
      Build the base docker compose command for a Phlo project.

      <PySourceCode>
        ```python
        def compose_base_cmd(
            *,
            phlo_dir: Path,
            project_name: str,
            profiles: Iterable[str] = (),
        ) -> list[str]:
            """Build the base docker compose command for a Phlo project.

            Args:
                phlo_dir: Directory containing compose and environment files.
                project_name: Docker compose project name.
                profiles: Optional compose profile names to enable.

            Returns:
                Base command tokens for docker compose invocation.
            """
            compose_file = phlo_dir / "docker-compose.yml"
            env_file = phlo_dir / ".env"
            env_local_file = phlo_dir / ".env.local"

            cmd = [
                "docker",
                "compose",
                "-p",
                project_name,
                "-f",
                str(compose_file),
                "--env-file",
                str(env_file),
            ]

            if env_local_file.exists():
                cmd.extend(["--env-file", str(env_local_file)])

            for profile in profiles:
                cmd.extend(["--profile", profile])

            return cmd
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;phlo_dir&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Directory containing compose and environment files.
        </PyParameter>

        <PyParameter name="&#x22;project_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          Docker compose project name.
        </PyParameter>

        <PyParameter name="&#x22;profiles&#x22;" type="&#x22;Iterable[str]&#x22;" value="&#x22;()&#x22;">
          Optional compose profile names to enable.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        Base command tokens for docker compose invocation.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
