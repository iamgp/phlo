# command (/docs/python-reference/core/phlo/cli/infrastructure/command)



<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;CommandError&#x22;" href="&#x22;/docs/python-reference/core/phlo/cli/infrastructure/command/CommandError&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;run_command&#x22;" type="&#x22;(cmd, *, timeout_seconds=None, cwd=None, env=None, capture_output=True, check=True) -> CompletedProcess[str]&#x22;">
      Run a subprocess command with optional timeout and environment overrides.

      <PySourceCode>
        ```python
        def run_command(
            cmd: Sequence[str],
            *,
            timeout_seconds: int | None = None,
            cwd: str | None = None,
            env: Mapping[str, str] | None = None,
            capture_output: bool = True,
            check: bool = True,
        ) -> CompletedProcess[str]:
            """Run a subprocess command with optional timeout and environment overrides.

            Args:
                cmd: Command and arguments to execute.
                timeout_seconds: Optional timeout in seconds.
                cwd: Optional working directory.
                env: Optional environment overrides.
                capture_output: Whether to capture stdout/stderr.
                check: Whether to raise on non-zero exit codes.

            Returns:
                CompletedProcess containing stdout, stderr, returncode, and args.

            Raises:
                CommandError: When check is True and the command exits non-zero.
                subprocess.TimeoutExpired: When the command exceeds timeout_seconds.
            """
            command_name = cmd[0] if cmd else "<empty>"
            logger.debug(
                "subprocess_command_started",
                command_name=command_name,
                arg_count=max(len(cmd) - 1, 0),
                cwd=cwd,
                timeout_seconds=timeout_seconds,
                capture_output=capture_output,
            )

            result = subprocess.run(
                list(cmd),
                capture_output=capture_output,
                text=capture_output,
                timeout=timeout_seconds,
                cwd=cwd,
                env=None if env is None else dict(env),
                check=False,
            )
            stdout = result.stdout or ""
            stderr = result.stderr or ""
            if check and result.returncode != 0:
                logger.error(
                    "subprocess_command_failed",
                    command_name=command_name,
                    returncode=result.returncode,
                    stdout_length=len(stdout),
                    stderr_length=len(stderr),
                )
                raise CommandError(
                    cmd=tuple(cmd),
                    returncode=result.returncode,
                    stdout=stdout,
                    stderr=stderr,
                )
            logger.debug(
                "subprocess_command_completed",
                command_name=command_name,
                returncode=result.returncode,
            )
            return result
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;cmd&#x22;" type="&#x22;Sequence[str]&#x22;" value="undefined">
          Command and arguments to execute.
        </PyParameter>

        <PyParameter name="&#x22;timeout_seconds&#x22;" type="&#x22;int | None&#x22;" value="&#x22;None&#x22;">
          Optional timeout in seconds.
        </PyParameter>

        <PyParameter name="&#x22;cwd&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
          Optional working directory.
        </PyParameter>

        <PyParameter name="&#x22;env&#x22;" type="&#x22;Mapping[str, str] | None&#x22;" value="&#x22;None&#x22;">
          Optional environment overrides.
        </PyParameter>

        <PyParameter name="&#x22;capture_output&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
          Whether to capture stdout/stderr.
        </PyParameter>

        <PyParameter name="&#x22;check&#x22;" type="&#x22;bool&#x22;" value="&#x22;True&#x22;">
          Whether to raise on non-zero exit codes.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;subprocess.CompletedProcess&#x22;">
        CompletedProcess containing stdout, stderr, returncode, and args.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
