"""Service hooks for Nessie.

This module provides lifecycle hooks for Nessie service initialization,
including branch creation and bootstrap operations. Hooks ensure required
branches (main, dev) exist and have baseline commits.

The hooks CLI is used by the Docker entrypoint and service initialization
to prepare Nessie before other services depend on it.

Example:
    $ python -m phlo_nessie.hooks init-branches

Functions:
    init_branches: Ensure Nessie main/dev branches exist and are bootstrapped.
    main: CLI entrypoint for hooks execution.

"""

from __future__ import annotations

import argparse
import json
import time
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from phlo.config.env import load_project_env
from phlo.logging import get_logger

logger = get_logger(__name__)
_DEFAULT_WAREHOUSE = "s3://lake/warehouse"


def _get_json(url: str) -> dict[str, Any]:
    """Perform a JSON GET request.

    Executes an HTTP GET request with JSON Accept header and parses
    the response body as JSON.

    Args:
        url: URL to request.

    Returns:
        dict[str, Any]: Parsed JSON response payload.

    Raises:
        HTTPError: On non-2xx HTTP responses.
        URLError: On connection errors.
        json.JSONDecodeError: On invalid JSON response.

    Example:
        >>> data = _get_json("http://localhost:19120/api/v1/trees")
        >>> print(data.get("references", []))

    """
    logger.debug(
        "nessie_hooks_get_json_requested",
        url=url,
    )
    req = Request(url, headers={"Accept": "application/json"})
    with urlopen(req, timeout=5) as response:  # nosec B310
        payload = response.read().decode("utf-8")
    data = json.loads(payload)
    logger.debug(
        "nessie_hooks_get_json_succeeded",
        url=url,
        key_count=len(data.keys()),
    )
    return data


def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Perform a JSON POST request.

    Sends a JSON payload via HTTP POST and parses the response.

    Args:
        url: URL to request.
        payload: JSON payload to send.

    Returns:
        dict[str, Any]: Parsed JSON response payload, or empty dict for empty bodies.

    Raises:
        HTTPError: On non-2xx HTTP responses.
        URLError: On connection errors.
        json.JSONDecodeError: On invalid JSON response.

    Example:
        >>> result = _post_json(
        ...     "http://localhost:19120/api/v1/trees/tree",
        ...     {"type": "BRANCH", "name": "dev", "hash": "abc123"}
        ... )

    """
    logger.debug(
        "nessie_hooks_post_json_requested",
        url=url,
        payload_keys=sorted(payload.keys()),
    )
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=10) as response:  # nosec B310
        body = response.read().decode("utf-8")
    if not body:
        logger.debug(
            "nessie_hooks_post_json_succeeded",
            url=url,
            has_body=False,
        )
        return {}
    response_data = json.loads(body)
    logger.debug(
        "nessie_hooks_post_json_succeeded",
        url=url,
        has_body=True,
        key_count=len(response_data.keys()),
    )
    return response_data


def _delete(url: str) -> int:
    """Perform a DELETE request and return the HTTP status code.

    Args:
        url: URL to delete.

    Returns:
        int: HTTP status code from the response.

    Raises:
        HTTPError: On non-2xx HTTP responses.
        URLError: On connection errors.

    Example:
        >>> status = _delete("http://localhost:19120/api/v1/trees/branch/old")
        >>> print(status)
        204

    """
    logger.debug(
        "nessie_hooks_delete_requested",
        url=url,
    )
    req = Request(url, method="DELETE")
    with urlopen(req, timeout=10) as response:  # nosec B310
        status_code = response.getcode()
    logger.debug(
        "nessie_hooks_delete_succeeded",
        url=url,
        status_code=status_code,
    )
    return status_code


def _resolve_nessie_url() -> str:
    """Resolve the Nessie base URL from environment variables.

    Checks NESSIE_URL first, then falls back to localhost with
    NESSIE_PORT (defaulting to 19120).

    Returns:
        str: Nessie base URL without trailing slash.

    Example:
        >>> url = _resolve_nessie_url()
        'http://localhost:19120'

    """
    env = load_project_env()
    if url := env.get("NESSIE_URL"):
        return url.rstrip("/")
    port = env.get("NESSIE_PORT", "19120")
    return f"http://localhost:{port}"


def _get_ref_log(base_url: str, ref: str) -> list[dict[str, Any]]:
    """Return the Nessie commit log entries for a ref.

    Retrieves the most recent commit log entry for a given reference.

    Args:
        base_url: Nessie base URL.
        ref: Reference name (branch or tag).

    Returns:
        list[dict[str, Any]]: List of log entry dictionaries.

    Example:
        >>> log = _get_ref_log("http://localhost:19120", "main")
        >>> print(log[0].get("commitMeta", {}).get("message"))

    """
    payload = _get_json(f"{base_url}/api/v1/trees/tree/{ref}/log?maxRecords=1")
    log_entries = payload.get("logEntries", [])
    return log_entries if isinstance(log_entries, list) else []


def _get_iceberg_prefix(base_url: str, ref: str) -> str:
    """Resolve the Iceberg REST prefix for a Nessie ref.

    Fetches Iceberg catalog configuration and extracts the REST API prefix
    for the given reference.

    Args:
        base_url: Nessie base URL.
        ref: Reference name (branch or tag).

    Returns:
        str: Iceberg REST prefix string.

    Raises:
        RuntimeError: If prefix is missing from configuration.

    Example:
        >>> prefix = _get_iceberg_prefix("http://localhost:19120", "main")
        'main'

    """
    config = _get_json(f"{base_url}/iceberg/{ref}/v1/config?warehouse={_DEFAULT_WAREHOUSE}")
    defaults = config.get("defaults", {})
    prefix = defaults.get("prefix") if isinstance(defaults, dict) else None
    if not isinstance(prefix, str) or not prefix:
        raise RuntimeError(f"Missing Iceberg REST prefix for ref '{ref}'.")
    return prefix


def _delete_namespace_if_present(base_url: str, prefix: str, namespace: str) -> None:
    """Delete a bootstrap namespace when it already exists.

    Silently handles 404 errors (namespace not found) while raising
    other HTTP errors.

    Args:
        base_url: Nessie base URL.
        prefix: Iceberg REST prefix for the reference.
        namespace: Namespace name to delete.

    Raises:
        HTTPError: On non-404 HTTP errors.

    Example:
        >>> _delete_namespace_if_present(
        ...     "http://localhost:19120", "main", "__phlo_bootstrap_main__"
        ... )

    """
    namespace_url = f"{base_url}/iceberg/v1/{prefix}/namespaces/{namespace}"
    try:
        _delete(namespace_url)
    except HTTPError as exc:
        if exc.code != 404:
            raise


def _ensure_bootstrap_commit(base_url: str, ref: str) -> None:
    """Materialize a baseline catalog commit for refs with empty history.

    Creates a temporary namespace to force a commit on references that have
    no existing commits. This ensures the reference exists in the catalog
    and can be used for subsequent operations.

    Args:
        base_url: Nessie base URL.
        ref: Reference name to bootstrap.

    Example:
        >>> _ensure_bootstrap_commit("http://localhost:19120", "main")

    """
    if _get_ref_log(base_url, ref):
        logger.info(
            "nessie_hooks_bootstrap_commit_exists",
            base_url=base_url,
            ref=ref,
        )
        return

    prefix = _get_iceberg_prefix(base_url, ref)
    namespace = f"__phlo_bootstrap_{ref}__"
    namespace_url = f"{base_url}/iceberg/v1/{prefix}/namespaces"

    logger.info(
        "nessie_hooks_bootstrap_commit_started",
        base_url=base_url,
        ref=ref,
        namespace=namespace,
    )
    _delete_namespace_if_present(base_url, prefix, namespace)
    _post_json(namespace_url, {"namespace": [namespace]})
    _delete(f"{namespace_url}/{namespace}")
    logger.info(
        "nessie_hooks_bootstrap_commit_completed",
        base_url=base_url,
        ref=ref,
        namespace=namespace,
    )


def init_branches() -> int:
    """Ensure Nessie main/dev branches exist.

    Waits for Nessie service to be ready, then ensures both 'main' and 'dev'
    branches exist with bootstrap commits. Creates 'dev' from 'main' if
    it doesn't exist.

    This function is designed to be called from Docker entrypoints and
    service initialization scripts.

    Returns:
        int: Exit code (0 for success, non-zero for errors).

    Example:
        >>> exit_code = init_branches()
        >>> print(exit_code)
        0

    """
    # Initialization is deliberately best-effort: every failure path below logs
    # a warning and returns 0 so a slow or half-ready Nessie never fails the
    # surrounding service startup.
    base_url = _resolve_nessie_url()
    trees_url = f"{base_url}/api/v1/trees"
    logger.info(
        "nessie_hooks_init_branches_started",
        base_url=base_url,
    )

    for attempt in range(1, 31):
        try:
            data = _get_json(trees_url)
            if "references" in data:
                logger.info(
                    "nessie_hooks_nessie_ready",
                    base_url=base_url,
                    attempt=attempt,
                )
                break
        except Exception:
            logger.debug(
                "nessie_hooks_nessie_wait_retry",
                base_url=base_url,
                attempt=attempt,
                exc_info=True,
            )
            time.sleep(1)
    else:
        logger.warning(
            "nessie_hooks_nessie_not_ready",
            base_url=base_url,
            max_attempts=30,
        )
        return 0

    try:
        data = _get_json(trees_url)
        existing = {ref.get("name") for ref in data.get("references", [])}
    except Exception as exc:
        logger.warning(
            "nessie_hooks_list_branches_failed",
            base_url=base_url,
            error=str(exc),
            exc_info=True,
        )
        return 0

    if "main" not in existing:
        logger.warning(
            "nessie_hooks_main_branch_missing",
            base_url=base_url,
            existing_branch_count=len(existing),
        )
        return 0

    try:
        _ensure_bootstrap_commit(base_url, "main")
    except Exception as exc:
        logger.warning(
            "nessie_hooks_main_bootstrap_failed",
            base_url=base_url,
            error=str(exc),
            exc_info=True,
        )
        return 0

    if "dev" in existing:
        try:
            _ensure_bootstrap_commit(base_url, "dev")
        except Exception as exc:
            logger.warning(
                "nessie_hooks_dev_bootstrap_failed",
                base_url=base_url,
                error=str(exc),
                exc_info=True,
            )
            return 0
        logger.info(
            "nessie_hooks_dev_branch_exists",
            base_url=base_url,
        )
        return 0

    try:
        main_data = _get_json(f"{base_url}/api/v1/trees/tree/main")
        main_hash = main_data.get("hash")
        if not main_hash:
            logger.warning(
                "nessie_hooks_main_hash_missing",
                base_url=base_url,
            )
            return 0
        created = _post_json(
            f"{base_url}/api/v1/trees/tree",
            {"type": "BRANCH", "name": "dev", "hash": main_hash},
        )
        if created.get("name") == "dev":
            logger.info(
                "nessie_hooks_dev_branch_created",
                base_url=base_url,
                source_hash=main_hash,
            )
        else:
            logger.warning(
                "nessie_hooks_dev_branch_create_unexpected_payload",
                base_url=base_url,
                payload_keys=sorted(created.keys()),
            )
        _ensure_bootstrap_commit(base_url, "dev")
    except Exception as exc:
        logger.warning(
            "nessie_hooks_dev_branch_create_failed",
            base_url=base_url,
            error=str(exc),
            exc_info=True,
        )

    logger.info(
        "nessie_hooks_init_branches_completed",
        base_url=base_url,
    )
    return 0


def main() -> int:
    """Run the Nessie hooks CLI entrypoint.

    Parses command line arguments and dispatches to appropriate
    hook functions.

    Returns:
        int: Process exit code.

    Example:
        $ python -m phlo_nessie.hooks init-branches

    Commands:
        init-branches: Initialize main and dev branches.

    """
    parser = argparse.ArgumentParser(description="Phlo Nessie hooks")
    parser.add_argument("action", choices=["init-branches"])
    args = parser.parse_args()
    logger.info(
        "nessie_hooks_main_action_requested",
        action=args.action,
    )

    if args.action == "init-branches":
        return init_branches()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
