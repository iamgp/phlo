from __future__ import annotations

import json
import os
import subprocess
import time
from collections.abc import Mapping, Callable
from pathlib import Path
from typing import Any, List, Optional, Dict

from dagster import AssetKey

from phlo.transformer import BaseTransformer, TransformationResult
from phlo.hooks import (
    LineageEventContext,
    LineageEventEmitter,
    TelemetryEventContext,
    TelemetryEventEmitter,
    TransformEventContext,
    TransformEventEmitter,
)
from phlo_dbt.translator import CustomDbtTranslator


def _latest_project_mtime(dbt_project_path: Path) -> float:
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
    manifest_path = dbt_project_path / "target" / "manifest.json"

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


def _asset_key_to_str(asset_key: AssetKey) -> str:
    if hasattr(asset_key, "path") and asset_key.path:
        return ".".join(str(part) for part in asset_key.path)
    return str(asset_key)


def _emit_dbt_lineage(
    manifest_path: Path,
    translator: CustomDbtTranslator,
    *,
    lineage_emitter: LineageEventEmitter,
    logger: Any,
    reader: Callable[[str], Any],
) -> None:
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
        asset_keys[str(unique_id)] = _asset_key_to_str(asset_key)

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
        super().__init__(context, logger)
        self.project_dir = project_dir
        self.profiles_dir = profiles_dir
        self.target = target
        self.dbt_executable = dbt_executable

    def _run_command(
        self, args: List[str], env: Optional[Dict[str, str]] = None
    ) -> subprocess.CompletedProcess:
        full_env = os.environ.copy()
        if env:
            full_env.update(env)

        # Ensure DBT_PROFILES_DIR is set if not passed explicitly in args (though we pass it)
        # But for 'subprocess', arguments are better.

        self.logger.info(f"Running command: {self.dbt_executable} {' '.join(args)}")

        return subprocess.run(
            [self.dbt_executable] + args,
            cwd=str(self.project_dir),
            env=full_env,
            capture_output=True,
            text=True,
            check=False,
        )

    def run_transform(
        self, partition_key: Optional[str] = None, parameters: Dict[str, Any] = None
    ) -> TransformationResult:
        parameters = parameters or {}
        select_args = parameters.get("select", [])
        exclude_args = parameters.get("exclude", [])
        skip_build = parameters.get("skip_build", False)

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
            self.logger.info(f"Running dbt for partition: {partition_key}")

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

        # Only emit start if we're actually running build
        if not skip_build:
            emitter.emit_start()

        try:
            # 1. Run dbt build (unless skipped)
            if not skip_build:
                result = self._run_command(build_args)

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
            translator = CustomDbtTranslator()  # Uses default config logic internally

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

            return TransformationResult(
                status="success",
                models_built=-1,  # TODO: Parse from stdout if needed
                models_failed=0,
                tests_passed=-1,
                tests_failed=0,
                metadata={"total_elapsed_seconds": elapsed, "dbt_output": result.stdout},
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
