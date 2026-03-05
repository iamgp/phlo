from __future__ import annotations

import json
import os
import re
import subprocess
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from phlo.logging import log_event
from phlo.operations.transformation import BaseTransformer, TransformationResult
from phlo.hooks import (
    LineageEventContext,
    LineageEventEmitter,
    TelemetryEventContext,
    TelemetryEventEmitter,
    TransformEventContext,
    TransformEventEmitter,
)
from phlo_dbt.translator import DbtSpecTranslator
from phlo_dbt.runtime_config import ensure_dbt_profile


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
    if not manifest_path.exists():
        logger.warning("dbt manifest not found at %s; skipping lineage emit", manifest_path)
        return
    try:
        manifest = reader(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        logger.warning("Failed to read dbt manifest for lineage: %s", exc)
        return
    if not isinstance(manifest, Mapping):
        logger.warning("dbt manifest payload is not a mapping; skipping lineage emit")
        return

    nodes = manifest.get("nodes") or {}
    sources = manifest.get("sources") or {}
    if not isinstance(nodes, Mapping) or not isinstance(sources, Mapping):
        logger.warning("dbt manifest nodes or sources missing; skipping lineage emit")
        return

    asset_keys: dict[str, str] = {}
    for unique_id, props in {**nodes, **sources}.items():
        if not isinstance(props, Mapping):
            continue
        try:
            asset_key = translator.get_asset_key(props)
        except Exception:
            continue
        asset_keys[str(unique_id)] = str(asset_key)

    edges: list[tuple[str, str]] = []
    target_keys: list[str] = []
    for unique_id, props in nodes.items():
        if not isinstance(props, Mapping):
            continue
        resource_type = str(props.get("resource_type") or "")
        if resource_type not in {"model", "seed", "snapshot"}:
            continue
        target_key = asset_keys.get(str(unique_id))
        if not target_key:
            continue
        depends_on = props.get("depends_on") or {}
        depends_nodes = depends_on.get("nodes") or []
        if not isinstance(depends_nodes, list):
            continue
        for upstream_id in depends_nodes:
            source_key = asset_keys.get(str(upstream_id))
            if source_key:
                edges.append((source_key, target_key))
        target_keys.append(target_key)

    if edges:
        lineage_emitter.emit_edges(
            edges=edges,
            asset_keys=sorted(set(target_keys)),
            metadata={"source": "dbt", "manifest_path": str(manifest_path)},
        )


class DbtTransformer(BaseTransformer):
    """
    Phlo Transformer implementation for dbt.
    Encapsulates dbt execution logic and Phlo event emission.
    """

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

        emitter = TransformEventEmitter(
            TransformEventContext(
                tool="dbt",
                project_dir=str(self.project_dir),
                target=self.target,
                partition_key=partition_key,
                model_names=model_names,
                tags={"tool": "dbt"},
            )
        )
        telemetry = TelemetryEventEmitter(
            TelemetryEventContext(tags={"tool": "dbt", "target": self.target})
        )
        lineage = LineageEventEmitter(
            LineageEventContext(tags={"tool": "dbt", "target": self.target})
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
