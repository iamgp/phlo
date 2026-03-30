# DbtTransformer (/docs/python-reference/packages/phlo-dbt/phlo_dbt/transformer/DbtTransformer)



Phlo Transformer implementation for dbt.

Encapsulates dbt execution logic and Phlo event emission. This class
handles:

* dbt command execution (build, compile, docs generate)
* Profile and target management
* Partition-aware execution
* Event emission for lineage, telemetry, and transform tracking
* Result parsing and transformation result creation

The transformer integrates with Phlo's hook system to emit events for
lineage tracking, performance metrics, and execution monitoring. It
supports both local and containerized dbt execution environments.

Attributes [#attributes]

<PyAttribute name="&#x22;project_dir&#x22;" type="null" value="&#x22;project_dir&#x22;">
  Path to the dbt project directory.
</PyAttribute>

<PyAttribute name="&#x22;profiles_dir&#x22;" type="null" value="&#x22;profiles_dir&#x22;">
  Path to the dbt profiles directory.
</PyAttribute>

<PyAttribute name="&#x22;target&#x22;" type="null" value="&#x22;target&#x22;">
  dbt target profile name (default: "dev").
</PyAttribute>

<PyAttribute name="&#x22;dbt_executable&#x22;" type="null" value="&#x22;dbt_executable&#x22;">
  dbt binary name or path (default: "dbt").
</PyAttribute>

Functions [#functions]

<PyFunction name="&#x22;__init__&#x22;" type="&#x22;(self, context, logger, project_dir, profiles_dir, target='dev', dbt_executable='dbt')&#x22;">
  Initialize dbt transformer runtime configuration.

  <PySourceCode>
    ```python
    def __init__(
        self,
        context: Any,
        logger: Any,
        project_dir: Path,
        profiles_dir: Path,
        target: str = "dev",
        dbt_executable: str = "dbt",
    ):
        """Initialize dbt transformer runtime configuration.

        Args:
            context: Execution context passed from orchestrator.
            logger: Logger instance.
            project_dir: dbt project directory.
            profiles_dir: dbt profiles directory.
            target: dbt target profile name.
            dbt_executable: dbt binary name or path.

        """
        super().__init__(context, logger)
        self.project_dir = project_dir
        self.profiles_dir = profiles_dir
        self.target = target
        self.dbt_executable = dbt_executable
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;context&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Execution context passed from orchestrator.
    </PyParameter>

    <PyParameter name="&#x22;logger&#x22;" type="&#x22;Any&#x22;" value="undefined">
      Logger instance.
    </PyParameter>

    <PyParameter name="&#x22;project_dir&#x22;" type="&#x22;Path&#x22;" value="undefined">
      dbt project directory.
    </PyParameter>

    <PyParameter name="&#x22;profiles_dir&#x22;" type="&#x22;Path&#x22;" value="undefined">
      dbt profiles directory.
    </PyParameter>

    <PyParameter name="&#x22;target&#x22;" type="&#x22;str&#x22;" value="&#x22;'dev'&#x22;">
      dbt target profile name.
    </PyParameter>

    <PyParameter name="&#x22;dbt_executable&#x22;" type="&#x22;str&#x22;" value="&#x22;'dbt'&#x22;">
      dbt binary name or path.
    </PyParameter>
  </div>

  <PyFunctionReturn type="null" />
</PyFunction>

<PyFunction name="&#x22;_sanitize_command_args_for_logging&#x22;" type="&#x22;(args) -> list[str]&#x22;">
  Redact sensitive argument values before logging command invocations.

  <PySourceCode>
    ```python
    @staticmethod
    def _sanitize_command_args_for_logging(args: list[str]) -> list[str]:
        """Redact sensitive argument values before logging command invocations."""
        sensitive_flags = {
            "--vars",
            "--password",
            "--token",
            "--secret",
            "--key",
            "--access-token",
            "--api-key",
        }
        sensitive_prefixes = tuple(f"{flag}=" for flag in sensitive_flags)
        redacted_args: list[str] = []
        redact_next = False

        for arg in args:
            if redact_next:
                redacted_args.append("<redacted>")
                redact_next = False
                continue

            normalized = arg.lower()
            if normalized in sensitive_flags:
                redacted_args.append(arg)
                redact_next = True
                continue

            if normalized.startswith(sensitive_prefixes):
                key = arg.split("=", 1)[0]
                redacted_args.append(f"{key}=<redacted>")
                continue

            redacted_args.append(arg)

        return redacted_args
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;args&#x22;" type="&#x22;list[str]&#x22;" value="null" />
  </div>

  <PyFunctionReturn type="&#x22;list[str]&#x22;" />
</PyFunction>

<PyFunction name="&#x22;_run_command&#x22;" type="&#x22;(self, args, env=None) -> subprocess.CompletedProcess&#x22;">
  Run a dbt subprocess command inside the configured project.

  <PySourceCode>
    ```python
    def _run_command(
        self, args: list[str], env: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess:
        """Run a dbt subprocess command inside the configured project.

        Args:
            args: dbt command arguments.
            env: Optional environment variable overrides.

        Returns:
            Completed subprocess result.

        """
        full_env = os.environ.copy()
        if env:
            full_env.update(env)

        # Ensure DBT_PROFILES_DIR is set if not passed explicitly in args (though we pass it)
        # But for 'subprocess', arguments are better.

        log_event(
            self.logger,
            "info",
            "dbt_command_running",
            command_name=self.dbt_executable,
            command_args=self._sanitize_command_args_for_logging(args),
        )

        return subprocess.run(
            [self.dbt_executable] + args,
            cwd=str(self.project_dir),
            env=full_env,
            capture_output=True,
            text=True,
            check=False,
        )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;args&#x22;" type="&#x22;list[str]&#x22;" value="undefined">
      dbt command arguments.
    </PyParameter>

    <PyParameter name="&#x22;env&#x22;" type="&#x22;dict[str, str] | None&#x22;" value="&#x22;None&#x22;">
      Optional environment variable overrides.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;subprocess.CompletedProcess&#x22;">
    Completed subprocess result.
  </PyFunctionReturn>
</PyFunction>

<PyFunction name="&#x22;run_transform&#x22;" type="&#x22;(self, partition_key=None, parameters=None) -> TransformationResult&#x22;">
  Execute dbt build/docs flow and emit transform telemetry events.

  <PySourceCode>
    ```python
    def run_transform(
        self, partition_key: str | None = None, parameters: dict[str, Any] | None = None
    ) -> TransformationResult:
        """Execute dbt build/docs flow and emit transform telemetry events.

        Args:
            partition_key: Optional partition date key for dbt vars.
            parameters: Optional runtime parameters controlling dbt execution.

        Returns:
            Transformation result containing status, counts, and metadata.

        """
        parameters = parameters or {}
        select_args = parameters.get("select", [])
        exclude_args = parameters.get("exclude", [])
        skip_build = parameters.get("skip_build", False)
        ensure_dbt_profile(self.profiles_dir, runtime=self.context, target=self.target)

        # Build dbt args
        build_args = [
            "build",
            "--profiles-dir",
            str(self.profiles_dir),
            "--target",
            self.target,
        ]

        if select_args:
            build_args.append("--select")
            build_args.extend(select_args)

        if exclude_args:
            build_args.append("--exclude")
            build_args.extend(exclude_args)

        if partition_key:
            build_args.extend(["--vars", f'{{"partition_date_str": "{partition_key}"}}'])
            log_event(
                self.logger,
                "info",
                "dbt_partition_execution_started",
                partition_key=partition_key,
            )

        # Setup Emitters
        # We need model names for context. If select args are passed, we use those as proxy
        # or we might parse the output.
        model_names = select_args if select_args else ["all"]
        run_id = getattr(self.context, "run_id", None)
        asset_key = getattr(self.context, "asset_key", None)
        resolved_asset_key = None
        if asset_key is not None:
            if hasattr(asset_key, "to_user_string"):
                resolved_asset_key = str(asset_key.to_user_string())
            else:
                resolved_asset_key = str(asset_key)
        correlation = HookCorrelation(
            run_id=run_id,
            asset_key=resolved_asset_key,
            partition_key=partition_key,
            job_name=getattr(self.context, "job_name", None),
        )

        emitter = TransformEventEmitter(
            TransformEventContext(
                tool="dbt",
                project_dir=str(self.project_dir),
                target=self.target,
                partition_key=partition_key,
                asset_key=resolved_asset_key,
                run_id=run_id,
                model_names=model_names,
                tags={"tool": "dbt"},
                correlation=correlation,
            )
        )
        telemetry = TelemetryEventEmitter(
            TelemetryEventContext(
                tags={"tool": "dbt", "target": self.target},
                correlation=correlation,
            )
        )
        lineage = LineageEventEmitter(
            LineageEventContext(
                tags={"tool": "dbt", "target": self.target}, correlation=correlation
            )
        )

        start_time = time.time()
        elapsed = 0.0
        result_stdout = ""

        # Only emit start if we're actually running build
        if not skip_build:
            emitter.emit_start()

        try:
            # 1. Run dbt build (unless skipped)
            if not skip_build:
                result = self._run_command(build_args)
                result_stdout = result.stdout

                if result.returncode != 0:
                    raise RuntimeError(
                        f"dbt build failed: {result.stderr}\nSTDOUT: {result.stdout}"
                    )

                elapsed = time.time() - start_time

                # 2. Emit Success Metrics
                emitter.emit_end(status="success", metrics={"dbt_args": build_args})
                telemetry.emit_metric(
                    name="transform.duration_seconds",
                    value=elapsed,
                    unit="seconds",
                    payload={"models": model_names},
                )

            # 3. Emit Lineage
            # We assume manifest is at target/manifest.json
            manifest_path = self.project_dir / "target" / "manifest.json"
            translator = DbtSpecTranslator()

            _emit_dbt_lineage(
                manifest_path,
                translator,
                lineage_emitter=lineage,
                logger=self.logger,
                reader=json.loads,
            )

            # 4. Generate Docs (Optional, but legacy implementation did it)
            # We skip it for optimization unless requested, but to match legacy behavior:
            if parameters.get("generate_docs", True):
                docs_args = [
                    "docs",
                    "generate",
                    "--profiles-dir",
                    str(self.profiles_dir),
                    "--target",
                    self.target,
                ]
                self._run_command(docs_args)
                # We don't fail hard on docs gen failure usually

            if skip_build:
                elapsed = time.time() - start_time

            summary = _parse_dbt_summary(result_stdout)
            counts_source = "skip_build"
            counts = {
                "models_built": 0,
                "models_failed": 0,
                "tests_passed": 0,
                "tests_failed": 0,
            }
            if not skip_build:
                counts_source = "run_results"
                counts = _read_run_results_counts(
                    self.project_dir / "target" / "run_results.json"
                ) or {
                    "models_built": -1,
                    "models_failed": -1,
                    "tests_passed": -1,
                    "tests_failed": -1,
                }
                if counts["models_built"] < 0:
                    counts_source = "summary_only_combined"

            return TransformationResult(
                status="success",
                models_built=counts["models_built"],
                models_failed=counts["models_failed"],
                tests_passed=counts["tests_passed"],
                tests_failed=counts["tests_failed"],
                metadata={
                    "total_elapsed_seconds": elapsed,
                    "dbt_output": result_stdout,
                    "dbt_summary": summary,
                    "counts_source": counts_source,
                },
            )

        except Exception as exc:
            elapsed = time.time() - start_time
            emitter.emit_end(status="failure", error=str(exc))
            telemetry.emit_log(
                name="transform.failure",
                level="error",
                payload={
                    "error": str(exc),
                    "elapsed_seconds": elapsed,
                    "models": model_names,
                },
            )
            return TransformationResult(
                status="failure",
                models_built=0,
                models_failed=0,
                tests_passed=0,
                tests_failed=0,
                metadata={"error": str(exc)},
                error=str(exc),
            )
    ```
  </PySourceCode>

  <div>
    <PyParameter name="&#x22;self&#x22;" type="null" value="null" />

    <PyParameter name="&#x22;partition_key&#x22;" type="&#x22;str | None&#x22;" value="&#x22;None&#x22;">
      Optional partition date key for dbt vars.
    </PyParameter>

    <PyParameter name="&#x22;parameters&#x22;" type="&#x22;dict[str, Any] | None&#x22;" value="&#x22;None&#x22;">
      Optional runtime parameters controlling dbt execution.
    </PyParameter>
  </div>

  <PyFunctionReturn type="&#x22;phlo.operations.transformation.TransformationResult&#x22;">
    Transformation result containing status, counts, and metadata.
  </PyFunctionReturn>
</PyFunction>
