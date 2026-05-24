#!/bin/sh
set -e

if [ "$PHLO_DEV_MODE" = "true" ] && [ -f /opt/phlo-dev/pyproject.toml ]; then
    echo "Dev mode: installing local phlo workspace packages..."
    uv pip install --system -e /opt/phlo-dev >/tmp/phlo-api-dev-install.log 2>&1 || cat /tmp/phlo-api-dev-install.log
    if [ -f /opt/phlo-dev/packages/phlo-api/pyproject.toml ]; then
        uv pip install --system -e /opt/phlo-dev/packages/phlo-api >/tmp/phlo-api-package-install.log 2>&1 || cat /tmp/phlo-api-package-install.log
    fi
    for package_dir in /opt/phlo-dev/packages/phlo-*; do
        if [ "$package_dir" = "/opt/phlo-dev/packages/phlo-api" ]; then
            continue
        fi
        if [ -f "$package_dir/pyproject.toml" ]; then
            package_name="$(basename "$package_dir")"
            uv pip install --system -e "$package_dir" \
                >/tmp/"$package_name"-install.log 2>&1 || cat /tmp/"$package_name"-install.log
        fi
    done
    export PYTHONPATH="/opt/phlo-dev/src:/opt/phlo-dev/packages/phlo-api/src:${PYTHONPATH:-/app}"
fi

exec "$@"
