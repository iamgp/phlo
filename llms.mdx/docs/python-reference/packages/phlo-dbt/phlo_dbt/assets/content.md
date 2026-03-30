# assets (/docs/python-reference/packages/phlo-dbt/phlo_dbt/assets)



dbt asset specification builders for Phlo.

This module provides functionality to discover and build Phlo asset specifications
from dbt project manifests. It handles manifest parsing, dependency resolution,
and runtime execution of dbt models within the Phlo orchestration framework.

Example:

> > > from phlo\_dbt.assets import build\_dbt\_asset\_specs
> > > specs = build\_dbt\_asset\_specs()
> > > for spec in specs:
> > > ...     print(f"Asset: \{spec.key}, Group: \{spec.group}")

<PyAttribute name="&#x22;logger&#x22;" type="null" value="&#x22;get_logger(__name__)&#x22;" />

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;_raise_required_dbt_setup_error&#x22;" type="&#x22;(*, reason, dbt_project_path, dbt_profiles_path, manifest_path) -> None&#x22;">
      Raise a required capability setup error for dbt asset discovery.

      <PySourceCode>
        ```python
        def _raise_required_dbt_setup_error(
            *,
            reason: str,
            dbt_project_path: Path,
            dbt_profiles_path: Path,
            manifest_path: Path,
        ) -> None:
            """Raise a required capability setup error for dbt asset discovery."""
            raise PhloCapabilitySetupError(
                capability="dbt",
                required=True,
                message=f"dbt asset discovery failed: {reason}",
                suggestions=[
                    f"Check the dbt project at {dbt_project_path}",
                    f"Check generated profiles at {dbt_profiles_path}",
                    f"Ensure dbt can compile a valid manifest at {manifest_path}",
                ],
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;reason&#x22;" type="&#x22;str&#x22;" value="null" />

        <PyParameter name="&#x22;dbt_project_path&#x22;" type="&#x22;Path&#x22;" value="null" />

        <PyParameter name="&#x22;dbt_profiles_path&#x22;" type="&#x22;Path&#x22;" value="null" />

        <PyParameter name="&#x22;manifest_path&#x22;" type="&#x22;Path&#x22;" value="null" />
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;" />
    </PyFunction>

    <PyFunction name="&#x22;_asset_deps&#x22;" type="&#x22;(unique_id, nodes, asset_keys) -> list[str]&#x22;">
      Resolve upstream asset dependencies for a dbt node.

      <PySourceCode>
        ```python
        def _asset_deps(unique_id: str, nodes: Mapping[str, Any], asset_keys: dict[str, str]) -> list[str]:
            """Resolve upstream asset dependencies for a dbt node.

            Args:
                unique_id: dbt unique node identifier.
                nodes: Manifest node mapping.
                asset_keys: Mapping of dbt unique IDs to asset keys.

            Returns:
                Upstream asset keys for the node.

            """
            props = nodes.get(unique_id, {})
            depends_on = props.get("depends_on") or {}
            depends_nodes = depends_on.get("nodes") or []
            deps: list[str] = []
            if isinstance(depends_nodes, list):
                for upstream_id in depends_nodes:
                    key = asset_keys.get(str(upstream_id))
                    if key:
                        deps.append(key)
            return deps
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;unique_id&#x22;" type="&#x22;str&#x22;" value="undefined">
          dbt unique node identifier.
        </PyParameter>

        <PyParameter name="&#x22;nodes&#x22;" type="&#x22;Mapping[str, Any]&#x22;" value="undefined">
          Manifest node mapping.
        </PyParameter>

        <PyParameter name="&#x22;asset_keys&#x22;" type="&#x22;dict[str, str]&#x22;" value="undefined">
          Mapping of dbt unique IDs to asset keys.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        Upstream asset keys for the node.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;_run_dbt_model&#x22;" type="&#x22;(*, model_name, project_dir, profiles_dir, runtime) -> list[MaterializeResult]&#x22;">
      Execute a single dbt model and map result to materialization output.

      <PySourceCode>
        ```python
        def _run_dbt_model(
            *,
            model_name: str,
            project_dir: Path,
            profiles_dir: Path,
            runtime: RuntimeContext,
        ) -> list[MaterializeResult]:
            """Execute a single dbt model and map result to materialization output.

            Args:
                model_name: dbt model name to execute.
                project_dir: dbt project root.
                profiles_dir: dbt profiles directory.
                runtime: Asset runtime context.

            Returns:
                Materialization results for the model run.

            """
            target = resolve_dbt_target_name(runtime)
            partition_key = runtime.partition_key

            transformer = DbtTransformer(
                context=runtime,
                logger=runtime.logger,
                project_dir=project_dir,
                profiles_dir=profiles_dir,
                target=target,
            )

            result = transformer.run_transform(
                partition_key=partition_key,
                parameters={"select": [model_name]},
            )

            return [
                MaterializeResult(
                    status=result.status,
                    metadata={
                        "model": model_name,
                        "dbt_target": target,
                        "dbt_status": result.status,
                        "dbt_metadata": result.metadata,
                    },
                )
            ]
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;model_name&#x22;" type="&#x22;str&#x22;" value="undefined">
          dbt model name to execute.
        </PyParameter>

        <PyParameter name="&#x22;project_dir&#x22;" type="&#x22;Path&#x22;" value="undefined">
          dbt project root.
        </PyParameter>

        <PyParameter name="&#x22;profiles_dir&#x22;" type="&#x22;Path&#x22;" value="undefined">
          dbt profiles directory.
        </PyParameter>

        <PyParameter name="&#x22;runtime&#x22;" type="&#x22;RuntimeContext&#x22;" value="undefined">
          Asset runtime context.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;list&#x22;">
        Materialization results for the model run.
      </PyFunctionReturn>
    </PyFunction>

    <PyFunction name="&#x22;build_dbt_asset_specs&#x22;" type="&#x22;() -> list[AssetSpec]&#x22;">
      Build asset specifications from dbt manifest metadata.

      <PySourceCode>
        ```python
        def build_dbt_asset_specs() -> list[AssetSpec]:
            """Build asset specifications from dbt manifest metadata.

            Returns:
                Asset specs representing supported dbt nodes.

            """
            settings = get_settings()

            dbt_project_path = settings.dbt_project_path
            dbt_profiles_path = settings.dbt_profiles_path
            manifest_path = dbt_project_path / "target" / "manifest.json"

            if not dbt_project_path.exists() or not (dbt_project_path / "dbt_project.yml").exists():
                logger.warning(
                    "optional_capability_degraded",
                    capability="dbt",
                    reason="project_missing",
                    dbt_project_path=str(dbt_project_path),
                )
                return []

            ensure_dbt_profile(dbt_profiles_path)

            if not ensure_dbt_manifest(dbt_project_path, dbt_profiles_path):
                _raise_required_dbt_setup_error(
                    reason="manifest_unavailable",
                    dbt_project_path=dbt_project_path,
                    dbt_profiles_path=dbt_profiles_path,
                    manifest_path=manifest_path,
                )

            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                _raise_required_dbt_setup_error(
                    reason="manifest_read_failed",
                    dbt_project_path=dbt_project_path,
                    dbt_profiles_path=dbt_profiles_path,
                    manifest_path=manifest_path,
                )

            if not isinstance(manifest, Mapping):
                _raise_required_dbt_setup_error(
                    reason="manifest_not_mapping",
                    dbt_project_path=dbt_project_path,
                    dbt_profiles_path=dbt_profiles_path,
                    manifest_path=manifest_path,
                )

            translator = DbtSpecTranslator()
            nodes = manifest.get("nodes")
            sources = manifest.get("sources")
            if nodes is None:
                nodes = {}
            if sources is None:
                sources = {}
            if not isinstance(nodes, Mapping) or not isinstance(sources, Mapping):
                _raise_required_dbt_setup_error(
                    reason="manifest_shape_invalid",
                    dbt_project_path=dbt_project_path,
                    dbt_profiles_path=dbt_profiles_path,
                    manifest_path=manifest_path,
                )

            asset_keys: dict[str, str] = {}
            for unique_id, props in {**nodes, **sources}.items():
                if not isinstance(props, Mapping):
                    continue
                try:
                    asset_key = translator.get_asset_key(props)
                except Exception:
                    logger.exception(
                        "dbt_asset_specs_asset_key_translate_failed",
                        unique_id=str(unique_id),
                    )
                    continue
                asset_keys[str(unique_id)] = str(asset_key)

            specs: list[AssetSpec] = []
            for unique_id, props in nodes.items():
                if not isinstance(props, Mapping):
                    continue
                resource_type = str(props.get("resource_type") or "")
                if resource_type not in {"model", "seed", "snapshot"}:
                    continue
                asset_key = asset_keys.get(str(unique_id))
                if not asset_key:
                    continue
                model_name = str(props.get("name") or asset_key)
                deps = _asset_deps(str(unique_id), nodes, asset_keys)
                description = translator.get_description(props)
                group = translator.get_group_name(props)
                kinds = translator.get_kinds(props)
                metadata = translator.get_metadata(props)
                tags = {"tool": "dbt"}

                def _runner(runtime: RuntimeContext, model=model_name) -> list[MaterializeResult]:
                    """Execute one dbt-backed asset run.

                    Args:
                        runtime: Asset runtime context.
                        model: Bound dbt model name for this spec.

                    Returns:
                        Materialization results for the selected dbt model.

                    """
                    return _run_dbt_model(
                        model_name=model,
                        project_dir=dbt_project_path,
                        profiles_dir=dbt_profiles_path,
                        runtime=runtime,
                    )

                specs.append(
                    AssetSpec(
                        key=asset_key,
                        group=group,
                        description=description,
                        kinds=kinds,
                        tags=tags,
                        metadata=metadata,
                        partitions=PartitionSpec(kind="daily"),
                        deps=deps,
                        run=RunSpec(fn=_runner),
                    )
                )

            logger.info(
                "dbt_asset_specs_built",
                spec_count=len(specs),
                dbt_project_path=str(dbt_project_path),
            )
            return specs
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;list&#x22;">
        Asset specs representing supported dbt nodes.
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
