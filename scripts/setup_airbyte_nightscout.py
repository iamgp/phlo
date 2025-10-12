#!/usr/bin/env python3
"""
Setup Airbyte connection for Nightscout data ingestion.

This script automates the creation of:
- Source: Nightscout API
- Destination: Local JSON files
- Connection: Nightscout to Local JSON

Usage:
    python scripts/setup_airbyte_nightscout.py --nightscout-url <your-url> --api-secret <secret>
"""

from __future__ import annotations

import argparse
import sys
import time

import requests


AIRBYTE_API_BASE = "http://localhost:8001"
DEFAULT_WORKSPACE_NAME = "default"


def wait_for_airbyte(timeout: int = 60) -> bool:
    """Wait for Airbyte API to be ready."""
    print("Waiting for Airbyte API to be ready...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{AIRBYTE_API_BASE}/api/v1/health", timeout=2)
            if response.status_code == 200:
                print("✓ Airbyte API is ready")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(2)

    print("✗ Timeout waiting for Airbyte API")
    return False


def get_workspace_id() -> str | None:
    """Get the workspace ID."""
    try:
        response = requests.post(
            f"{AIRBYTE_API_BASE}/api/v1/workspaces/list",
            json={},
            timeout=10,
        )
        response.raise_for_status()
        workspaces = response.json().get("workspaces", [])

        if not workspaces:
            print("✗ No workspaces found")
            return None

        workspace = workspaces[0]
        workspace_id = workspace["workspaceId"]
        workspace_name = workspace.get("name", "unknown")
        print(f"✓ Found workspace: {workspace_name} ({workspace_id})")
        return workspace_id

    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to get workspace: {e}")
        return None


def get_source_definition_id(name: str) -> str | None:
    """Get source definition ID by name."""
    try:
        response = requests.post(
            f"{AIRBYTE_API_BASE}/api/v1/source_definitions/list",
            json={},
            timeout=10,
        )
        response.raise_for_status()
        definitions = response.json().get("sourceDefinitions", [])

        for definition in definitions:
            if name.lower() in definition.get("name", "").lower():
                return definition["sourceDefinitionId"]

        return None

    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to get source definitions: {e}")
        return None


def get_destination_definition_id(name: str) -> str | None:
    """Get destination definition ID by name."""
    try:
        response = requests.post(
            f"{AIRBYTE_API_BASE}/api/v1/destination_definitions/list",
            json={},
            timeout=10,
        )
        response.raise_for_status()
        definitions = response.json().get("destinationDefinitions", [])

        for definition in definitions:
            if name.lower() in definition.get("name", "").lower():
                return definition["destinationDefinitionId"]

        return None

    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to get destination definitions: {e}")
        return None


def create_source(
    workspace_id: str,
    nightscout_url: str,
    api_secret: str | None = None,
) -> str | None:
    """Create Nightscout source."""
    print("\nCreating Nightscout source...")

    # Use File (CSV, JSON, etc.) source for custom API
    source_def_id = get_source_definition_id("file")

    if not source_def_id:
        print("✗ Could not find File source definition")
        print("Creating generic HTTP source instead...")
        # Fallback to creating with manifest
        return create_custom_nightscout_source(workspace_id, nightscout_url, api_secret)

    config = {
        "dataset_name": "nightscout_entries",
        "url": f"{nightscout_url}/api/v1/entries.json",
        "format": "json",
        "provider": {
            "storage": "HTTPS",
        },
        "reader_options": "{}",
    }

    try:
        response = requests.post(
            f"{AIRBYTE_API_BASE}/api/v1/sources/create",
            json={
                "workspaceId": workspace_id,
                "sourceDefinitionId": source_def_id,
                "connectionConfiguration": config,
                "name": "Nightscout API",
            },
            timeout=10,
        )
        response.raise_for_status()
        source_id = response.json()["sourceId"]
        print(f"✓ Created Nightscout source: {source_id}")
        return source_id

    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to create source: {e}")
        if hasattr(e.response, "text"):
            print(f"  Response: {e.response.text}")
        return None


def create_custom_nightscout_source(
    workspace_id: str,
    nightscout_url: str,
    api_secret: str | None = None,
) -> str | None:
    """Create custom Nightscout source using declarative manifest."""
    print("Creating custom Nightscout connector...")

    # Load the manifest
    import json
    from pathlib import Path

    manifest_path = Path(__file__).parent.parent / "airbyte" / "nightscout-connector-manifest.yaml"

    if not manifest_path.exists():
        print(f"✗ Manifest not found at {manifest_path}")
        return None

    try:
        response = requests.post(
            f"{AIRBYTE_API_BASE}/api/v1/sources/create_custom",
            json={
                "workspaceId": workspace_id,
                "name": "Nightscout API",
                "manifest": manifest_path.read_text(),
                "config": {
                    "nightscout_url": nightscout_url,
                    "api_secret": api_secret or "",
                },
            },
            timeout=10,
        )
        response.raise_for_status()
        source_id = response.json()["sourceId"]
        print(f"✓ Created custom Nightscout source: {source_id}")
        return source_id

    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to create custom source: {e}")
        return None


def create_destination(workspace_id: str) -> str | None:
    """Create Local JSON destination."""
    print("\nCreating Local JSON destination...")

    dest_def_id = get_destination_definition_id("local json")

    if not dest_def_id:
        print("✗ Could not find Local JSON destination definition")
        return None

    config = {
        "destination_path": "/data/airbyte/json_data",
    }

    try:
        response = requests.post(
            f"{AIRBYTE_API_BASE}/api/v1/destinations/create",
            json={
                "workspaceId": workspace_id,
                "destinationDefinitionId": dest_def_id,
                "connectionConfiguration": config,
                "name": "Local JSON",
            },
            timeout=10,
        )
        response.raise_for_status()
        destination_id = response.json()["destinationId"]
        print(f"✓ Created Local JSON destination: {destination_id}")
        return destination_id

    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to create destination: {e}")
        if hasattr(e.response, "text"):
            print(f"  Response: {e.response.text}")
        return None


def create_connection(
    workspace_id: str,
    source_id: str,
    destination_id: str,
) -> str | None:
    """Create connection between source and destination."""
    print("\nCreating connection...")

    # First, discover schema from source
    try:
        discover_response = requests.post(
            f"{AIRBYTE_API_BASE}/api/v1/sources/discover_schema",
            json={
                "sourceId": source_id,
            },
            timeout=30,
        )
        discover_response.raise_for_status()
        catalog = discover_response.json().get("catalog")

        if not catalog:
            print("✗ No catalog discovered from source")
            return None

        print("✓ Discovered source schema")

    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to discover schema: {e}")
        return None

    # Create connection
    try:
        response = requests.post(
            f"{AIRBYTE_API_BASE}/api/v1/connections/create",
            json={
                "name": "Nightscout to Local JSON",
                "sourceId": source_id,
                "destinationId": destination_id,
                "syncCatalog": catalog,
                "scheduleType": "manual",
                "status": "active",
                "namespaceDefinition": "destination",
                "namespaceFormat": "${SOURCE_NAMESPACE}",
            },
            timeout=10,
        )
        response.raise_for_status()
        connection_id = response.json()["connectionId"]
        print(f"✓ Created connection: {connection_id}")
        return connection_id

    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to create connection: {e}")
        if hasattr(e.response, "text"):
            print(f"  Response: {e.response.text}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Setup Airbyte Nightscout connection"
    )
    parser.add_argument(
        "--nightscout-url",
        required=True,
        help="Nightscout instance URL (e.g., https://your-instance.herokuapp.com)",
    )
    parser.add_argument(
        "--api-secret",
        help="Nightscout API secret (optional if public)",
    )
    parser.add_argument(
        "--wait",
        type=int,
        default=60,
        help="Seconds to wait for Airbyte to be ready (default: 60)",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Airbyte Nightscout Connection Setup")
    print("=" * 60)

    # Wait for Airbyte
    if not wait_for_airbyte(timeout=args.wait):
        sys.exit(1)

    # Get workspace
    workspace_id = get_workspace_id()
    if not workspace_id:
        sys.exit(1)

    # Create source
    source_id = create_source(workspace_id, args.nightscout_url, args.api_secret)
    if not source_id:
        sys.exit(1)

    # Create destination
    destination_id = create_destination(workspace_id)
    if not destination_id:
        sys.exit(1)

    # Create connection
    connection_id = create_connection(workspace_id, source_id, destination_id)
    if not connection_id:
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✓ Setup complete!")
    print("=" * 60)
    print(f"\nConnection ID: {connection_id}")
    print(f"Nightscout URL: {args.nightscout_url}")
    print(f"\nNext steps:")
    print(f"1. Visit http://localhost:8000 to view the connection")
    print(f"2. Run a sync manually to test")
    print(f"3. View in Dagster at http://localhost:3000")


if __name__ == "__main__":
    main()
