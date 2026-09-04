"""Static blueprint contract for the Retail Files blueprint.

The contract is the machine-checkable record of ADR 0052 (Retail Files
blueprint distribution): exact released phlo-family pins, the frozen
third-party allowlist, the bounded-starter evidence facts, and a stable
digest over the packaged template resources. It is committed, not generated;
`resource_digest()` recomputes the digest from the shipped resources so tests
can prove the contract stays current.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
RESOURCES_DIR = PACKAGE_DIR / "resources" / "retail_files"
CONTRACT_PATH = PACKAGE_DIR / "blueprint_contract.json"


def load_contract() -> dict:
    """Return the static blueprint contract document."""
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def resource_digest() -> str:
    """Compute the stable digest over the packaged template resources.

    The digest is the SHA-256 of the canonical JSON array of
    ``[relative-posix-path, sha256(file-bytes)]`` pairs sorted by path, so it
    changes only when resource bytes change and is stable across machines.
    """
    entries: list[list[str]] = []
    for path in sorted(RESOURCES_DIR.rglob("*")):
        if path.is_file():
            entries.append(
                [
                    path.relative_to(RESOURCES_DIR).as_posix(),
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                ]
            )
    canonical = json.dumps(entries, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"
