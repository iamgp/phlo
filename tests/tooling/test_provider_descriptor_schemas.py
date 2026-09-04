"""Static descriptor/conformance schema and bundling tests (#855, ADR 0053).

Pins: the three strict canonical schemas exist and are byte-identical to
their packaged copies; the v2 registry schema makes tier and support
fields unexpressible; canonical and bundled v2 registry data validate;
the static generator is deterministic and imports no provider module.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
SCHEMA_DIR = ROOT / "registry/schema"
BUNDLED_SCHEMA_DIR = ROOT / "src/phlo/plugins/schemas"
FIXTURES = ROOT / "tests/fixtures/provider_tiers"
SCRIPT = ROOT / "scripts/validate_provider_descriptors.py"
VALIDATOR_SCRIPT = ROOT / "scripts/validate_support_manifest.py"

SCHEMA_FILES = ("descriptor.v1.json", "conformance-result.v1.json", "registry.v2.json")

SPEC = importlib.util.spec_from_file_location("_descriptor_validator", SCRIPT)
assert SPEC and SPEC.loader
DESCRIPTOR_VALIDATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = DESCRIPTOR_VALIDATOR
SPEC.loader.exec_module(DESCRIPTOR_VALIDATOR)

VALIDATOR_SPEC = importlib.util.spec_from_file_location(
    "_support_manifest_validator_for_tiers", VALIDATOR_SCRIPT
)
assert VALIDATOR_SPEC and VALIDATOR_SPEC.loader
VALIDATOR = importlib.util.module_from_spec(VALIDATOR_SPEC)
sys.modules[VALIDATOR_SPEC.name] = VALIDATOR
VALIDATOR_SPEC.loader.exec_module(VALIDATOR)

validate_manifest = VALIDATOR.validate_manifest


def _schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


# --- Schema existence and packaging ---------------------------------------------------


@pytest.mark.parametrize("name", SCHEMA_FILES)
def test_canonical_schema_has_byte_identical_bundled_copy(name: str) -> None:
    assert (BUNDLED_SCHEMA_DIR / name).read_bytes() == (SCHEMA_DIR / name).read_bytes()


def test_all_three_strict_canonical_schemas_are_packaged() -> None:
    bundled = {path.name for path in BUNDLED_SCHEMA_DIR.glob("*.json")}
    assert set(SCHEMA_FILES) <= bundled


# --- Authors cannot set tier or support -----------------------------------------------


@pytest.mark.parametrize(
    "field_name",
    ["tier", "support", "verified", "release_supported", "conformance_tested", "legacy_verified"],
)
def test_descriptor_schema_rejects_every_tier_synonym(field_name: str) -> None:
    payload = _fixture("descriptor.valid.json")
    payload[field_name] = True
    errors = DESCRIPTOR_VALIDATOR.registry_v2_errors(
        {
            "$schema": "https://registry.phlohouse.com/schema/registry.v2.json",
            "schema_version": "2",
            "compatibility_epoch": 1,
            "updated_at": "2026-09-04T00:00:00Z",
            "plugins": {"acme": payload},
        },
        {name: _schema(name) for name in SCHEMA_FILES},
    )
    assert any(f"unknown property {field_name!r}" in error for error in errors)


def test_container_schema_rejects_per_entry_legacy_verified() -> None:
    payload = _fixture("descriptor.valid.json")
    payload["legacy_verified"] = True
    errors = DESCRIPTOR_VALIDATOR.registry_v2_errors(
        {
            "$schema": "https://registry.phlohouse.com/schema/registry.v2.json",
            "schema_version": "2",
            "compatibility_epoch": 1,
            "updated_at": "2026-09-04T00:00:00Z",
            "plugins": {"acme": payload},
        },
        {name: _schema(name) for name in SCHEMA_FILES},
    )
    assert any("unknown property 'legacy_verified'" in error for error in errors)


def test_descriptor_schema_self_check_passes() -> None:
    schemas = {name: _schema(name) for name in SCHEMA_FILES}
    assert DESCRIPTOR_VALIDATOR.schema_self_check_errors(schemas) == []


# --- Canonical/bundled v2 registry data ------------------------------------------------


def _v2_document() -> dict:
    return _fixture("registry-v2.canonical.json")


def test_canonical_v2_registry_data_validates() -> None:
    errors = DESCRIPTOR_VALIDATOR.registry_v2_errors(
        _v2_document(), {name: _schema(name) for name in SCHEMA_FILES}
    )
    assert errors == []


def test_bundled_v2_registry_data_is_byte_identical_to_canonical() -> None:
    assert (FIXTURES / "registry-v2.bundled.json").read_bytes() == (
        FIXTURES / "registry-v2.canonical.json"
    ).read_bytes()


def test_v2_registry_data_rejects_schema_version_drift() -> None:
    document = _v2_document()
    document["schema_version"] = "3"
    errors = DESCRIPTOR_VALIDATOR.registry_v2_errors(
        document, {name: _schema(name) for name in SCHEMA_FILES}
    )
    assert any("schema_version" in error for error in errors)


# --- Static generator: deterministic bundling, zero provider execution -----------------


def _run_script(
    *arguments: str, env_extra: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_script_validates_the_real_estate_and_reports_honest_tiers() -> None:
    result = _run_script("--check-bundled")
    assert result.returncode == 0, result.stderr
    assert "31 legacy_verified" in result.stdout
    assert "0 conformance-tested" in result.stdout
    assert "0 release-supported" in result.stdout


def test_script_emission_is_deterministic(tmp_path: Path) -> None:
    first, second = tmp_path / "a.json", tmp_path / "b.json"
    assert _run_script("--emit-v2", str(first)).returncode == 0
    assert _run_script("--emit-v2", str(second)).returncode == 0
    assert first.read_bytes() == second.read_bytes()
    emitted = json.loads(first.read_text(encoding="utf-8"))
    errors = DESCRIPTOR_VALIDATOR.registry_v2_errors(
        emitted, {name: _schema(name) for name in SCHEMA_FILES}
    )
    assert errors == []


def test_script_rejects_mutated_bundled_copy(tmp_path: Path) -> None:
    bundled = BUNDLED_SCHEMA_DIR / "descriptor.v1.json"
    original = bundled.read_bytes()
    try:
        bundled.write_bytes(original + b"\n")
        result = _run_script("--check-bundled")
        assert result.returncode == 1
        assert "byte-identical" in result.stderr
    finally:
        bundled.write_bytes(original)
    assert _run_script("--check-bundled").returncode == 0


def test_validation_subprocess_imports_no_fixture_provider_module() -> None:
    """The no-import proof: run static validation with an untrusted fixture
    provider module on PYTHONPATH; if any validation path imported provider
    code, the module would leave its marker behind."""
    marker = FIXTURES / "untrusted" / "imported.marker"
    if marker.exists():
        marker.unlink()
    try:
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            env={
                "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                "PYTHONPATH": str(FIXTURES / "untrusted"),
            },
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert not marker.exists(), "static validation imported the fixture provider module"
    finally:
        if marker.exists():
            marker.unlink()


# --- Support-manifest validator epoch + tier checks ------------------------------------


def test_support_manifest_validator_reports_zero_release_supported_at_head() -> None:
    assert VALIDATOR.registry_tier_errors(ROOT) == []
    summary = VALIDATOR.registry_tier_errors.last_summary
    assert "0 conformance-tested" in summary
    assert "0 release-supported" in summary


def test_support_manifest_validator_flags_epoch_mismatch(tmp_path: Path) -> None:
    schema = json.loads((SCHEMA_DIR / "registry.v2.json").read_text(encoding="utf-8"))
    schema["properties"]["compatibility_epoch"]["const"] = 2
    drifted = tmp_path / "registry.v2.json"
    drifted.write_text(json.dumps(schema), encoding="utf-8")
    original = VALIDATOR.REGISTRY_V2_SCHEMA_PATH
    try:
        VALIDATOR.REGISTRY_V2_SCHEMA_PATH = drifted
        errors = VALIDATOR.registry_tier_errors(ROOT)
        assert any("compatibility_epoch" in error for error in errors)
    finally:
        VALIDATOR.REGISTRY_V2_SCHEMA_PATH = original


def test_support_manifest_validator_flags_registry_trust_fields(tmp_path: Path) -> None:
    mirror = tmp_path / "repo"
    mirror.mkdir()
    # registry/ must be a REAL copy: the validator reads it, and this test
    # mutates the copy — symlinking would mutate the live tree.
    shutil.copytree(ROOT / "registry", mirror / "registry")
    for name in (".github", "packages", "src"):
        (mirror / name).symlink_to(ROOT / name, target_is_directory=True)
    shutil.copy2(ROOT / "README.md", mirror / "README.md")
    (mirror / "pyproject.toml").symlink_to(ROOT / "pyproject.toml")

    registry_path = mirror / "registry/plugins.json"
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    data["plugins"]["dagster"]["release_supported"] = True
    registry_path.write_text(json.dumps(data), encoding="utf-8")

    errors = VALIDATOR.registry_tier_errors(mirror)
    assert any("'release_supported'" in error and "not expressible" in error for error in errors)
    # The real tree is untouched.
    assert VALIDATOR.registry_tier_errors(ROOT) == []


def test_manifest_validation_still_green_with_tier_checks() -> None:
    manifest = json.loads((ROOT / "registry/support/v1.json").read_text(encoding="utf-8"))
    assert validate_manifest(manifest) == []
