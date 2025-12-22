#!/bin/bash
# Phlo Dagster Entrypoint
# Syncs dependencies in dev mode before running the main command

set -e

# If dev mode is enabled, sync dependencies from mounted pyproject.toml
if [ "$PHLO_DEV_MODE" = "true" ] && [ -f /opt/phlo-dev/pyproject.toml ]; then
    echo "Dev mode: syncing dependencies from pyproject.toml..."
    # Extract and install dependencies from the mounted pyproject.toml
    # Using uv pip install with --system to install into the container's Python
    cd /opt/phlo-dev
    uv pip install --system -e . 2>/dev/null || uv pip install --system . || echo "Warning: Could not sync dependencies"
    cd /opt/dagster
    echo "Dev mode: dependencies synced"
fi

# Execute the main command
exec "$@"
