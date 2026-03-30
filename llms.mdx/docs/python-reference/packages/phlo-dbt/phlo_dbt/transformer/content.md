# transformer (/docs/python-reference/packages/phlo-dbt/phlo_dbt/transformer)



dbt transformer implementation for Phlo orchestration.

This module provides the DbtTransformer class which executes dbt commands
within the Phlo transformation framework. It handles dbt build execution,
event emission for lineage and telemetry, and result parsing.

Example:

> > > from phlo\_dbt.transformer import DbtTransformer
> > > from pathlib import Path
> > >
> > > transformer = DbtTransformer(
> > > ...     context=dagster\_context,
> > > ...     logger=logger,
> > > ...     project\_dir=Path("workflows/transforms/dbt"),
> > > ...     profiles\_dir=Path("workflows/transforms/dbt/profiles"),
> > > ...     target="prod"
> > > ... )
> > >
> > > result = transformer.run\_transform(
> > > ...     partition\_key="2024-01-01",
> > > ...     parameters=\{"select": \["mrt\_orders"]}
> > > ... )
> > >
> > > print(f"Status: \{result.status}")
> > > print(f"Models built: \{result.models\_built}")
> > > print(f"Tests passed: \{result.tests\_passed}")

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;DbtTransformer&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dbt/phlo_dbt/transformer/DbtTransformer&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_parse_dbt_summary&#x22;" type="&#x22;(stdout) -> dict[str, int]&#x22;">
      Parse dbt build summary line: PASS=N WARN=N ERROR=N SKIP=N TOTAL=N.

      <PySourceCode>
        ```python
        def _parse_dbt_summary(stdout: str) -> dict[str, int]:
            """Parse dbt build summary line: PASS=N WARN=N ERROR=N SKIP=N TOTAL=N."""
            match = re.search(
                r"PASS=(\d+)\s+WARN=(\d+)\s+ERROR=(\d+)\s+SKIP=(\d+)\s+TOTAL=(\d+)",
                stdout,
            )
            if not match:
                return {"pass": 0, "warn": 0, "error": 0, "skip": 0, "total": 0}
            return {
                "pass": int(match.group(1)),
                "warn": int(match.group(2)),
                "error": int(match.group(3)),
                "skip": int(match.group(4)),
                "total": int(match.group(5)),
            }
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;stdout&#x22;" type="&#x22;str&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;dict[str, int]&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_resource_type_for_result&#x22;" type="&#x22;(result) -> str&#x22;">
      Infer dbt resource type from a run result mapping.

      <PySourceCode>
        ```python
        def _resource_type_for_result(result: Mapping[str, Any]) -> str:
            """Infer dbt resource type from a run result mapping.

            Args:
                result: Single result item from dbt run results.

            Returns:
                Resource type value, or an empty string if unavailable.

            """
            resource_type = result.get("resource_type")
            if isinstance(resource_type, str) and resource_type:
                return resource_type
            unique_id = result.get("unique_id")
            if isinstance(unique_id, str) and "." in unique_id:
                return unique_id.split(".", 1)[0]
            return ""
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;result&#x22;" type="&#x22;Mapping[str, Any]&#x22;" value="undefined">
          Single result item from dbt run results.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;str&#x22;">
        Resource type value, or an empty string if unavailable.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_parse_run_results_counts&#x22;" type="&#x22;(payload) -> dict[str, int] | None&#x22;">
      Extract model and test pass/fail counts from dbt run results payload.

      <PySourceCode>
        ```python
        def _parse_run_results_counts(payload: Mapping[str, Any]) -> dict[str, int] | None:
            """Extract model and test pass/fail counts from dbt run results payload.

            Args:
                payload: Parsed JSON payload from ``run_results.json``.

            Returns:
                Count mapping when parseable; otherwise ``None``.

            """
            results = payload.get("results")
            if not isinstance(results, list):
                return None

            counts = {
                "models_built": 0,
                "models_failed": 0,
                "tests_passed": 0,
                "tests_failed": 0,
            }
            model_types = {"model", "seed", "snapshot"}
            success_statuses = {"pass", "success"}
            skipped_statuses = {"skip", "skipped"}

            for item in results:
                if not isinstance(item, Mapping):
                    continue

                status = str(item.get("status") or "").strip().lower()
                resource_type = _resource_type_for_result(item)

                if resource_type in model_types:
                    if status in success_statuses:
                        counts["models_built"] += 1
                    elif status not in skipped_statuses:
                        counts["models_failed"] += 1
                    continue

                if resource_type == "test":
                    if status in success_statuses:
                        counts["tests_passed"] += 1
                    elif status not in skipped_statuses:
                        counts["tests_failed"] += 1

            return counts
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;payload&#x22;" type="&#x22;Mapping[str, Any]&#x22;" value="undefined">
          Parsed JSON payload from `run_results.json`.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict[str, int] | None&#x22;">
        Count mapping when parseable; otherwise `None`.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_read_run_results_counts&#x22;" type="&#x22;(path) -> dict[str, int] | None&#x22;">
      Read dbt run results counts from disk.

      <PySourceCode>
        ```python
        def _read_run_results_counts(path: Path) -> dict[str, int] | None:
            """Read dbt run results counts from disk.

            Args:
                path: Path to ``run_results.json``.

            Returns:
                Parsed count mapping when available; otherwise ``None``.

            """
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                return None
            if not isinstance(payload, Mapping):
                return None
            return _parse_run_results_counts(payload)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;path&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Path to `run_results.json`.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;dict[str, int] | None&#x22;">
        Parsed count mapping when available; otherwise `None`.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_latest_project_mtime&#x22;" type="&#x22;(dbt_project_path) -> float&#x22;">
      Return latest modification time across key dbt project files.

      <PySourceCode>
        ```python
        def _latest_project_mtime(dbt_project_path: Path) -> float:
            """Return latest modification time across key dbt project files.

            Args:
                dbt_project_path: Path to the dbt project root.

            Returns:
                Unix timestamp of the newest relevant file modification.

            """
            candidates: list[Path] = [
                dbt_project_path / "dbt_project.yml",
                dbt_project_path / "packages.yml",
                dbt_project_path / "package-lock.yml",
            ]
            candidate_dirs = [
                dbt_project_path / "models",
                dbt_project_path / "macros",
                dbt_project_path / "seeds",
                dbt_project_path / "snapshots",
                dbt_project_path / "tests",
                dbt_project_path / "analysis",
            ]

            latest = 0.0
            for path in candidates:
                if path.exists():
                    latest = max(latest, path.stat().st_mtime)

            for directory in candidate_dirs:
                if not directory.exists():
                    continue
                for file_path in directory.rglob("*"):
                    if file_path.is_file():
                        latest = max(latest, file_path.stat().st_mtime)

            return latest
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;dbt_project_path&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Path to the dbt project root.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;float&#x22;">
        Unix timestamp of the newest relevant file modification.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;ensure_dbt_manifest&#x22;" type="&#x22;(dbt_project_path, profiles_path) -> bool&#x22;">
      Ensure dbt manifest exists and is valid for the project.

      <PySourceCode>
        ```python
        def ensure_dbt_manifest(dbt_project_path: Path, profiles_path: Path) -> bool:
            """Ensure dbt manifest exists and is valid for the project.

            Args:
                dbt_project_path: Path to the dbt project root.
                profiles_path: Path to the dbt profiles directory.

            Returns:
                ``True`` when a valid manifest is present after checks/compile.

            """
            manifest_path = dbt_project_path / "target" / "manifest.json"
            ensure_dbt_profile(profiles_path)

            needs_compile = not manifest_path.exists()
            if not needs_compile:
                try:
                    needs_compile = _latest_project_mtime(dbt_project_path) > manifest_path.stat().st_mtime
                except OSError:
                    needs_compile = True

            if not needs_compile:
                try:
                    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    needs_compile = True
                else:
                    if not isinstance(manifest_payload, Mapping):
                        needs_compile = True

            if not needs_compile:
                return True

            try:
                result = subprocess.run(
                    ["dbt", "compile", "--profiles-dir", str(profiles_path)],
                    cwd=str(dbt_project_path),
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
            except FileNotFoundError:
                return False
            except subprocess.TimeoutExpired:
                return False

            if result.returncode != 0 or not manifest_path.exists():
                return False

            try:
                manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                return False

            return isinstance(manifest_payload, Mapping)
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;dbt_project_path&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Path to the dbt project root.
        </PyParameter>

        <PyParameter name="&#x22;profiles_path&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Path to the dbt profiles directory.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;bool&#x22;">
        `True` when a valid manifest is present after checks/compile.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_emit_dbt_lineage&#x22;" type="&#x22;(manifest_path, translator, *, lineage_emitter, logger, reader) -> None&#x22;">
      Emit lineage edges from a dbt manifest.

      <PySourceCode>
        ```python
        def _emit_dbt_lineage(
            manifest_path: Path,
            translator: DbtSpecTranslator,
            *,
            lineage_emitter: LineageEventEmitter,
            logger: Any,
            reader: Callable[[str], Any],
        ) -> None:
            """Emit lineage edges from a dbt manifest.

            Args:
                manifest_path: Path to ``manifest.json``.
                translator: Translator used to derive asset keys.
                lineage_emitter: Lineage event emitter instance.
                logger: Logger used for warning output.
                reader: JSON loader callable for manifest text.

            """
            manifest = load_dbt_manifest(manifest_path)
            if manifest is None:
                return

            edges, target_keys = collect_asset_lineage(manifest, translator=translator)

            if edges:
                lineage_emitter.emit_edges(
                    edges=edges,
                    asset_keys=target_keys,
                    metadata={"source": "dbt", "manifest_path": str(manifest_path)},
                )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;manifest_path&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Path to `manifest.json`.
        </PyParameter>

        <PyParameter name="&#x22;translator&#x22;" type="&#x22;DbtSpecTranslator&#x22;" value="undefined">
          Translator used to derive asset keys.
        </PyParameter>

        <PyParameter name="&#x22;lineage_emitter&#x22;" type="&#x22;LineageEventEmitter&#x22;" value="undefined">
          Lineage event emitter instance.
        </PyParameter>

        <PyParameter name="&#x22;logger&#x22;" type="&#x22;Any&#x22;" value="undefined">
          Logger used for warning output.
        </PyParameter>

        <PyParameter name="&#x22;reader&#x22;" type="&#x22;Callable[[str], Any]&#x22;" value="undefined">
          JSON loader callable for manifest text.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
