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
    uv pip install --system -e ".[defaults]" 2>/dev/null || \
      uv pip install --system -e . 2>/dev/null || \
      uv pip install --system . || \
      echo "Warning: Could not sync dependencies"
    cd /opt/dagster
    echo "Dev mode: dependencies synced"
fi

# Create sitecustomize.py to suppress Dagster SupersessionWarning at Python startup
# This runs before any Python script and filters out deprecated CLI warnings
SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")
cat > "${SITE_PACKAGES}/sitecustomize.py" << 'EOF'
# Phlo: Suppress Dagster deprecation warnings for deprecated CLI commands
import warnings
try:
    from dagster import SupersessionWarning
    warnings.filterwarnings("ignore", category=SupersessionWarning)
except ImportError:
    pass
EOF

# Execute the main command
exec "$@"
