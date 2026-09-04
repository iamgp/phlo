#!/usr/bin/env python3
"""Statically validate provider descriptors and conformance-result shapes.

Implements the static half of ADR 0053 (issue #855): strict canonical
schemas for publisher descriptors (Authority A), conformance results
(Authority B shape), and the v2 registry container; deterministic
bundling of packaged schema copies; and emission of the v2 view of the
legacy v1 registry with honest one-epoch ``legacy_verified``
normalization. Nothing here executes provider code: the only inputs read
are JSON schema and registry documents, and no plugin module, entry
point, or fixture provider is ever imported.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "registry" / "schema"
CANONICAL_REGISTRY = ROOT / "registry" / "plugins.json"
BUNDLED_SCHEMA_DIR = ROOT / "src" / "phlo" / "plugins" / "schemas"
BUNDLED_REGISTRY = ROOT / "src" / "phlo" / "plugins" / "registry_data.json"

SCHEMA_FILES = ("descriptor.v1.json", "conformance-result.v1.json", "registry.v2.json")

#: Fields that would let a registry author assert a tier or support fact.
#: The v2 descriptor field set must never contain any of these (ADR 0053
#: concern 3), under any spelling.
TIER_SYNONYM_FIELDS = frozenset(
    {
        "verified",
        "tier",
        "tiers",
        "support",
        "supported",
        "release_supported",
        "release-supported",
        "conformance_tested",
        "conformance-tested",
        "community",
        "legacy_verified",
        "legacy-verified",
        "certified",
        "approved",
        "trusted",
        "endorsement",
    }
)


def _load_validator_helpers() -> Any:
    """Reuse the support-manifest validator's minimal JSON Schema engine."""
    spec = importlib.util.spec_from_file_location(
        "_support_manifest_validator", ROOT / "scripts" / "validate_support_manifest.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_schemas() -> dict[str, dict[str, Any]]:
    schemas: dict[str, dict[str, Any]] = {}
    for name in SCHEMA_FILES:
        schemas[name] = json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))
    return schemas


def _resolve_file_refs(
    schema: dict[str, Any], schemas: dict[str, dict[str, Any]], root_name: str
) -> dict[str, Any]:
    """Inline-resolve sibling-file ``$ref`` targets into one document."""
    if isinstance(schema, dict):
        ref = schema.get("$ref")
        if isinstance(ref, str) and not ref.startswith("#/"):
            target_name = ref.split("#", 1)[0]
            if target_name not in schemas:
                raise ValueError(f"{root_name}: unresolved schema reference {ref!r}")
            return _resolve_file_refs(schemas[target_name], schemas, target_name)
        return {key: _resolve_file_refs(value, schemas, root_name) for key, value in schema.items()}
    if isinstance(schema, list):
        return [_resolve_file_refs(item, schemas, root_name) for item in schema]
    return schema


def schema_self_check_errors(schemas: dict[str, dict[str, Any]]) -> list[str]:
    """Check the frozen shapes themselves: no tier synonym may be
    expressible, and the container must pin the compatibility epoch."""
    errors: list[str] = []
    descriptor = schemas["descriptor.v1.json"]
    if descriptor.get("additionalProperties") is not False:
        errors.append("descriptor.v1.json: schema must reject unknown fields")
    properties = descriptor.get("properties", {})
    synonyms = TIER_SYNONYM_FIELDS & set(properties)
    if synonyms:
        errors.append(
            f"descriptor.v1.json: registry authors must not be able to express trust fields; "
            f"found {sorted(synonyms)!r}"
        )

    container = schemas["registry.v2.json"]
    container_properties = container.get("properties", {})
    epoch = container_properties.get("compatibility_epoch", {})
    if epoch.get("const") != 1:
        errors.append("registry.v2.json: compatibility_epoch must be pinned to 1")
    for schema_name in ("registry.v2.json", "conformance-result.v1.json"):
        if schemas[schema_name].get("additionalProperties") is not False:
            errors.append(f"{schema_name}: schema must reject unknown fields")
    legacy_block = (
        container_properties.get("legacy", {}).get("properties", {}).get("legacy_verified", {})
    )
    if "type" not in str(legacy_block) and legacy_block.get("items", {}).get("type") != "string":
        errors.append("registry.v2.json: legacy.legacy_verified must be a list of registry keys")
    return errors


def registry_v2_errors(
    v2_document: dict[str, Any], schemas: dict[str, dict[str, Any]]
) -> list[str]:
    """Validate a v2 registry document against the strict container schema."""
    helpers = _load_validator_helpers()
    merged = _resolve_file_refs(schemas["registry.v2.json"], schemas, "registry.v2.json")
    return helpers._schema_errors(v2_document, merged)


def normalize_v1_registry_document(data: dict[str, Any]) -> dict[str, Any]:
    """Import the pure normalizer from the packaged trust module."""
    spec = importlib.util.spec_from_file_location(
        "_phlo_trust", ROOT / "src" / "phlo" / "plugins" / "trust.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.normalize_v1_registry(data)


def validate_canonical_registry() -> list[str]:
    """Validate the checked-in v1 registry and its honest v2 normalization."""
    errors: list[str] = []
    v1 = json.loads(CANONICAL_REGISTRY.read_text(encoding="utf-8"))
    v2 = normalize_v1_registry_document(v1)
    errors.extend(registry_v2_errors(v2, _load_schemas()))

    legacy_claimed = set(v2.get("legacy", {}).get("legacy_verified", []))
    legacy_expected = {
        name for name, entry in v1.get("plugins", {}).items() if entry.get("verified") is True
    }
    if legacy_claimed != legacy_expected:
        errors.append(
            "legacy.legacy_verified must be exactly the v1 entries with verified: true "
            f"(derived, never asserted); expected {sorted(legacy_expected)!r}"
        )
    for name in v2["plugins"]:
        source_entry = v1["plugins"][name]
        for field_name in ("tier", "release_supported", "conformance_tested"):
            if field_name in source_entry:
                errors.append(
                    f"registry entry {name!r}: trust field {field_name!r} is not expressible"
                )
    return errors


def emit_v2() -> str:
    """Deterministically emit the v2 view of the canonical v1 registry."""
    v1 = json.loads(CANONICAL_REGISTRY.read_text(encoding="utf-8"))
    v2 = normalize_v1_registry_document(v1)
    return json.dumps(v2, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def bundle_check_errors() -> list[str]:
    """Bundled schema copies must be byte-identical to the canonical files."""
    errors: list[str] = []
    for name in SCHEMA_FILES:
        canonical = SCHEMA_DIR / name
        bundled = BUNDLED_SCHEMA_DIR / name
        if not bundled.is_file():
            errors.append(f"bundled schema copy missing: {bundled.relative_to(ROOT)}")
        elif bundled.read_bytes() != canonical.read_bytes():
            errors.append(
                f"bundled schema copy {bundled.relative_to(ROOT)} is not byte-identical to "
                f"{canonical.relative_to(ROOT)}"
            )
    if BUNDLED_REGISTRY.read_text(encoding="utf-8") != CANONICAL_REGISTRY.read_text(
        encoding="utf-8"
    ):
        errors.append(
            f"{BUNDLED_REGISTRY.relative_to(ROOT)} is stale; run generate_plugin_registry_data.py"
        )
    return errors


def main() -> int:
    """Run static descriptor validation; never import a provider module."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--emit-v2",
        metavar="PATH",
        type=Path,
        help="write the deterministic v2 view of the canonical registry to PATH",
    )
    parser.add_argument(
        "--check-bundled",
        action="store_true",
        help="verify packaged schema copies are byte-identical to the canonical schemas",
    )
    args = parser.parse_args()

    schemas = _load_schemas()
    errors = schema_self_check_errors(schemas)
    errors.extend(validate_canonical_registry())
    if args.check_bundled:
        errors.extend(bundle_check_errors())

    if args.emit_v2:
        args.emit_v2.write_text(emit_v2(), encoding="utf-8")

    if errors:
        print("provider descriptor validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    v1 = json.loads(CANONICAL_REGISTRY.read_text(encoding="utf-8"))
    legacy_count = len(v2_document_legacy(v1))
    print(
        f"validated provider descriptors: {len(v1.get('plugins', {}))} entries, "
        f"{legacy_count} legacy_verified, 0 conformance-tested, 0 release-supported"
    )
    return 0


def v2_document_legacy(v1: dict[str, Any]) -> list[str]:
    return sorted(
        name for name, entry in v1.get("plugins", {}).items() if entry.get("verified") is True
    )


if __name__ == "__main__":
    raise SystemExit(main())
