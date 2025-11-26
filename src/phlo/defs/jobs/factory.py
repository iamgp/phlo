# factory.py - Factory for job definitions from YAML configuration
# Creates Dagster job definitions from declarative YAML config

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any, Dict, List

import dagster as dg
from dagster import AssetKey

from phlo.defs.partitions import daily_partition


def _parse_asset_selection(selection_config: Dict[str, Any]) -> dg.AssetSelection:
    """Parse YAML asset selection config into Dagster AssetSelection."""
    selection_type = selection_config["type"]

    if selection_type == "group":
        groups = selection_config["groups"]
        return dg.AssetSelection.groups(*groups)
    elif selection_type == "keys":
        keys = selection_config["keys"]
        asset_keys = [AssetKey([key]) for key in keys]
        return dg.AssetSelection.keys(*asset_keys)
    elif selection_type == "mixed":
        selections = []
        if "keys" in selection_config:
            asset_keys = [AssetKey([key]) for key in selection_config["keys"]]
            selections.append(dg.AssetSelection.keys(*asset_keys))
        if "groups" in selection_config:
            selections.append(dg.AssetSelection.groups(*selection_config["groups"]))

        if len(selections) == 1:
            return selections[0]
        else:
            return selections[0] | selections[1]  # Combine selections
    else:
        raise ValueError(f"Unknown selection type: {selection_type}")


def create_jobs_from_config(config_path: Path | None = None) -> List[dg.UnresolvedAssetJobDefinition]:
    """Create job definitions from YAML configuration.
    
    Args:
        config_path: Path to config.yaml. If None, looks for config.yaml in same directory.
                     Returns empty list if config file doesn't exist.
    """
    if config_path is None:
        config_path = Path(__file__).parent / "config.yaml"
    
    if not config_path.exists():
        return []
    
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)

    jobs = []

    for job_key, job_config in config_data['jobs'].items():
        # Parse asset selection
        selection = _parse_asset_selection(job_config['selection'])

        # Parse partitions
        partitions_def = daily_partition if job_config.get('partitions') == 'daily' else None

        # Create job
        resources_config = job_config.get('resources', {})
        config = {"resources": resources_config} if resources_config else {}

        job = dg.define_asset_job(
            name=job_config['name'],
            description=job_config['description'],
            selection=selection,
            partitions_def=partitions_def,
            config=config,
        )

        jobs.append(job)

    return jobs
