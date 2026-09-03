"""Structural integration tests for the assembled Dagster Definitions.

Validates wiring contracts: asset graph shape, resource configuration,
check coverage, and schedule/sensor references. Requires dbt manifest
and workflow files to load definitions.
"""

import pytest

pytestmark = pytest.mark.integration

try:
    from phlo_dagster.framework.definitions import defs
except Exception as e:
    pytest.skip(f"Skipping module: dbt manifest not available ({e})", allow_module_level=True)

_assets = list(defs.assets or [])
if not _assets:
    pytest.skip(
        "Skipping module: no assets discovered. Ensure workflows are available.",
        allow_module_level=True,
    )


def _all_asset_keys() -> set:
    """Collect every AssetKey from the loaded definitions."""
    keys: set = set()
    for asset in _assets:
        if hasattr(asset, "keys"):
            keys |= set(asset.keys)
        else:
            k = getattr(asset, "key", None)
            if k:
                keys.add(k)
    return keys


def _publish_asset_keys() -> set:
    """Return asset keys whose path contains 'publish'."""
    return {k for k in _all_asset_keys() if "publish" in str(k)}


class TestDefinitionsStructure:
    """Validate the assembled Definitions object is wired correctly."""

    def test_definitions_have_assets_and_core_resources(self):
        """Core resources (trino) are present alongside discovered assets."""
        assert _assets, "expected at least one asset"
        resources = defs.resources or {}
        assert "trino" in resources, "trino resource must be registered"

    def test_asset_keys_are_unique(self):
        """Every asset key appears exactly once (no duplicates)."""
        seen: list[str] = []
        for asset in _assets:
            if hasattr(asset, "keys"):
                seen.extend(str(k) for k in asset.keys)
            else:
                k = getattr(asset, "key", None)
                if k:
                    seen.append(str(k))
        assert len(seen) == len(set(seen)), (
            f"duplicate asset keys: {[k for k in seen if seen.count(k) > 1]}"
        )

    def test_publish_assets_have_upstream_dependencies(self):
        """Publish assets are downstream of other assets (not isolated nodes)."""
        publish_keys = _publish_asset_keys()
        if not publish_keys:
            pytest.skip("no publish assets registered")
        all_keys = _all_asset_keys()
        assert publish_keys <= all_keys

        for asset in _assets:
            asset_keys = set(getattr(asset, "keys", []))
            if not asset_keys:
                k = getattr(asset, "key", None)
                asset_keys = {k} if k else set()
            if not asset_keys & publish_keys:
                continue
            deps = set(getattr(asset, "dependency_keys", []))
            assert deps, f"publish asset {asset_keys} has no upstream dependencies"

    def test_asset_checks_target_existing_assets(self):
        """Every registered asset check targets an asset that exists."""
        checks = list(defs.asset_checks or [])
        if not checks:
            pytest.skip("no asset checks registered")
        all_keys = _all_asset_keys()
        for check in checks:
            target = getattr(check, "asset_key", None)
            if target is not None:
                assert target in all_keys, f"check targets non-existent asset {target}"

    def test_resource_contract_fields(self):
        """Core resources expose required configuration fields."""
        resources = defs.resources or {}
        trino = resources.get("trino")
        if trino is None:
            pytest.skip("trino resource not registered")
        assert hasattr(trino, "user"), "trino resource must have user field"

        iceberg = resources.get("iceberg")
        if iceberg is not None:
            assert hasattr(iceberg, "ref"), "iceberg resource must have ref field"

    def test_schedules_reference_valid_jobs(self):
        """Every schedule references a job that exists in definitions."""
        schedules = list(defs.schedules or [])
        if not schedules:
            pytest.skip("no schedules registered")
        jobs = list(defs.jobs or [])
        job_names = {j.name for j in jobs if hasattr(j, "name")}
        for sched in schedules:
            job_name = getattr(sched, "job_name", None)
            if job_name:
                assert job_name in job_names, f"schedule references unknown job {job_name}"
            cron = getattr(sched, "cron_schedule", None)
            assert cron, f"schedule {getattr(sched, 'name', '?')} has empty cron_schedule"
