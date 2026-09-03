"""Polaris service lifecycle hooks (invoked via ``python -m phlo_polaris.hooks``).

``bootstrap`` waits for the Polaris API, then creates the Phlo catalog, the
writer and reader principals, and their grants. It is idempotent: existing
objects are reused, never recreated or deleted.
"""

from __future__ import annotations

import argparse
import sys
import time

from phlo.logging import get_logger

logger = get_logger(__name__)

BOOTSTRAP_TIMEOUT_SECONDS = 90


def wait_for_polaris(client, *, timeout_seconds: int = BOOTSTRAP_TIMEOUT_SECONDS) -> bool:
    """Poll the Polaris health endpoint until it responds or the timeout lapses."""
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if client.health_check():
            return True
        time.sleep(2)
    return False


def ensure_catalog(client, *, name: str, warehouse: str) -> bool:
    """Create the Phlo catalog when absent."""
    if client.get_catalog(name) is not None:
        logger.info("polaris_bootstrap_catalog_exists", catalog=name)
        return False
    client.create_catalog(name=name, warehouse=warehouse)
    logger.info("polaris_bootstrap_catalog_created", catalog=name)
    return True


def ensure_principal(client, *, name: str) -> bool:
    """Create one service principal when absent."""
    principals = {principal.get("principalName") for principal in client.list_principals()}
    if name in principals:
        logger.info("polaris_bootstrap_principal_exists", principal=name)
        return False
    client.create_principal(name=name)
    logger.info("polaris_bootstrap_principal_created", principal=name)
    return True


def bootstrap(client=None) -> int:
    """Bootstrap the Phlo realm objects in Polaris. Always exit 0 (best effort)."""
    if client is None:
        from phlo_polaris.resource import PolarisResource

        client = PolarisResource()
    if not wait_for_polaris(client):
        logger.warning("polaris_bootstrap_unavailable")
        return 0
    from phlo_polaris.settings import get_settings

    settings = get_settings()
    warehouse = f"s3://lake/warehouse/{settings.polaris_catalog}"
    ensure_catalog(client, name=settings.polaris_catalog, warehouse=warehouse)
    for principal in (
        settings.polaris_writer_client_id,
        settings.polaris_reader_client_id,
    ):
        ensure_principal(client, name=principal)
    grants = client.bootstrap_grants()
    logger.info("polaris_bootstrap_grants_applied", grants=grants)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="phlo_polaris.hooks")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("bootstrap", help="Create the Phlo catalog and principals")
    args = parser.parse_args(argv)
    if args.command == "bootstrap":
        return bootstrap()
    return 1


if __name__ == "__main__":
    sys.exit(main())
