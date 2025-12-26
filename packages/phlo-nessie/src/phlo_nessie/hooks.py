"""Service hooks for Nessie."""

from __future__ import annotations

import argparse
import json
import os
import time
from typing import Any
from urllib.request import Request, urlopen


def _get_json(url: str) -> dict[str, Any]:
    req = Request(url, headers={"Accept": "application/json"})
    with urlopen(req, timeout=5) as response:  # nosec B310
        payload = response.read().decode("utf-8")
    return json.loads(payload)


def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=10) as response:  # nosec B310
        body = response.read().decode("utf-8")
    if not body:
        return {}
    return json.loads(body)


def _resolve_nessie_url() -> str:
    if url := os.environ.get("NESSIE_URL"):
        return url.rstrip("/")
    port = os.environ.get("NESSIE_PORT", "19120")
    return f"http://localhost:{port}"


def init_branches() -> int:
    """Ensure Nessie main/dev branches exist."""
    base_url = _resolve_nessie_url()
    trees_url = f"{base_url}/api/v1/trees"

    for _ in range(30):
        try:
            data = _get_json(trees_url)
            if "references" in data:
                break
        except Exception:
            time.sleep(1)
    else:
        print("Warning: Nessie not ready; skipping branch initialization.")
        return 0

    try:
        data = _get_json(trees_url)
        existing = {ref.get("name") for ref in data.get("references", [])}
    except Exception as exc:
        print(f"Warning: Could not check Nessie branches: {exc}")
        return 0

    if "dev" in existing:
        print("Nessie branches ready (main, dev).")
        return 0

    if "main" not in existing:
        print("Warning: Nessie main branch missing; cannot create dev.")
        return 0

    try:
        main_data = _get_json(f"{base_url}/api/v1/trees/tree/main")
        main_hash = main_data.get("hash")
        if not main_hash:
            print("Warning: Nessie main branch hash missing; cannot create dev.")
            return 0
        created = _post_json(
            f"{base_url}/api/v1/trees/tree",
            {"type": "BRANCH", "name": "dev", "hash": main_hash},
        )
        if created.get("name") == "dev":
            print("Created Nessie 'dev' branch.")
        else:
            print("Warning: Nessie dev branch create did not return expected payload.")
    except Exception as exc:
        print(f"Warning: Could not create dev branch: {exc}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Phlo Nessie hooks")
    parser.add_argument("action", choices=["init-branches"])
    args = parser.parse_args()

    if args.action == "init-branches":
        return init_branches()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
