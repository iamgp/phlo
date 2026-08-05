#!/bin/bash
# Phlo Dagster Entrypoint
# Syncs dependencies in dev mode before running the main command

set -e

if [ "$(id -u)" -eq 0 ]; then

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

# In decoupled mode, runtime plugins live in /opt/phlo-dev/packages.
# Install every local workspace package so user workflows can import plugin modules.
if [ "$PHLO_DEV_MODE" = "true" ] && [ -d /opt/phlo-dev/packages ]; then
    echo "Dev mode: installing local workspace packages..."
    for pkg_dir in /opt/phlo-dev/packages/*; do
        if [ ! -d "$pkg_dir" ] || [ ! -f "$pkg_dir/pyproject.toml" ]; then
            continue
        fi
        uv pip install --system -e "$pkg_dir" || echo "Warning: Could not install $pkg_dir"
    done
    # Ensure core runtime plugins required by example projects are present.
    for required_pkg in \
        phlo-core-plugins \
        phlo-dagster \
        phlo-dlt \
        phlo-dbt \
        phlo-pandera \
        phlo-iceberg \
        phlo-nessie \
        phlo-trino \
        phlo-postgres \
        phlo-minio \
        phlo-lineage
    do
        required_path="/opt/phlo-dev/packages/$required_pkg"
        if [ -d "$required_path" ]; then
            uv pip install --system -e "$required_path" || echo "Warning: Could not install $required_pkg"
        fi
    done
    uv pip install --system dagster-dbt || echo "Warning: Could not install dagster-dbt"
    echo "Dev mode: local workspace packages installed"
fi

# Optionally install extra local packages in dev mode
if [ "$PHLO_DEV_MODE" = "true" ] && [ -n "$PHLO_DEV_EXTRA_PACKAGES" ]; then
    echo "Dev mode: installing extra packages: $PHLO_DEV_EXTRA_PACKAGES"
    for pkg in ${PHLO_DEV_EXTRA_PACKAGES//,/ }; do
        if [ -z "$pkg" ]; then
            continue
        fi
        local_path="/opt/phlo-dev/packages/$pkg"
        if [ -d "$local_path" ]; then
            uv pip install --system -e "$local_path" || echo "Warning: Could not install $pkg"
        else
            uv pip install --system "$pkg" || echo "Warning: Could not install $pkg"
        fi
    done
fi

# Install the mounted user project so workflow imports and project dependencies
# are available before Dagster loads Definitions.
if [ -f /app/pyproject.toml ]; then
    echo "Installing mounted Phlo project..."
    uv pip install --system -e /app
    echo "Mounted Phlo project installed"
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

else
    echo "Non-root mode: using mounted project directly"
fi

# Development stacks mount the complete repository. Make every source package
# importable even when the pinned runtime image runs as the unprivileged user
# and therefore cannot perform a system-wide editable install.
if [ "$PHLO_DEV_MODE" = "true" ] && [ -d /opt/phlo-dev ]; then
    for source_dir in /opt/phlo-dev/src /opt/phlo-dev/packages/*/src; do
        if [ -d "$source_dir" ]; then
            export PYTHONPATH="$source_dir${PYTHONPATH:+:$PYTHONPATH}"
        fi
    done
fi

# Execute Dagster from the mounted project root when available. User workflows
# often read local files relative to the project (for example data/*.csv), while
# DAGSTER_HOME intentionally remains /opt/dagster for instance state.
if [ -n "$PHLO_PROJECT_PATH" ] && [ -d "$PHLO_PROJECT_PATH" ]; then
    cd "$PHLO_PROJECT_PATH"
fi

# Execute the main command
exec "$@"
