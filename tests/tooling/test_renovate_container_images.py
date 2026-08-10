"""Semantic contracts for Renovate-managed package runtime images."""

from __future__ import annotations

import json
import re
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Any, cast

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "renovate.json"


def _manager() -> dict[str, Any]:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    managers = [
        manager
        for manager in config["customManagers"]
        if manager.get("customType") == "regex" and manager.get("datasourceTemplate") == "docker"
    ]
    assert len(managers) == 1
    return cast(dict[str, Any], managers[0])


def _python_regex(pattern: str) -> re.Pattern[str]:
    # Renovate uses RE2's JavaScript named-group spelling; Python uses ?P<name>.
    return re.compile(pattern.replace("(?<", "(?P<"))


def _image_patterns(manager: dict[str, Any]) -> list[re.Pattern[str]]:
    return [_python_regex(pattern) for pattern in manager["matchStrings"]]


def _image_match(manager: dict[str, Any], source: str) -> re.Match[str] | None:
    matches = [match for pattern in _image_patterns(manager) if (match := pattern.search(source))]
    assert len(matches) <= 1
    return matches[0] if matches else None


def test_runtime_image_manager_covers_only_recursive_package_source_yaml() -> None:
    manager = _manager()
    file_patterns = [_python_regex(pattern) for pattern in manager["managerFilePatterns"]]

    assert any(
        pattern.fullmatch("packages/phlo-postgres/src/phlo_postgres/service.yaml")
        for pattern in file_patterns
    )
    assert any(
        pattern.fullmatch("packages/phlo-openmetadata/src/phlo_openmetadata/setup/service.yml")
        for pattern in file_patterns
    )
    assert not any(
        pattern.fullmatch("packages/phlo-delta/tests/fixtures/delta_versions.yaml")
        for pattern in file_patterns
    )


def test_runtime_image_manager_extracts_every_real_immutable_root_image() -> None:
    manager = _manager()
    matched: set[Path] = set()
    eligible: set[Path] = set()

    for path in sorted((REPO_ROOT / "packages").glob("*/src/**/*.yaml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(document, dict) or not isinstance(document.get("image"), str):
            continue
        relative = path.relative_to(REPO_ROOT)
        if "@sha256:" in document["image"]:
            eligible.add(relative)
        match = _image_match(manager, path.read_text(encoding="utf-8"))
        if match:
            matched.add(relative)
            assert match.group("depName")
            assert match.group("currentValue")
            assert re.fullmatch(r"sha256:[0-9a-f]{64}", match.group("currentDigest"))

    assert matched == eligible


def test_runtime_image_replacement_updates_tag_and_digest_without_damaging_wrapper() -> None:
    manager = _manager()
    replacement = manager["autoReplaceStringTemplate"]

    def replace(source: str) -> str:
        match = _image_match(manager, source)
        assert match
        values = {"wrapperPrefix": "", "wrapperSuffix": ""}
        values.update({key: value or "" for key, value in match.groupdict().items()})
        values.update(newValue="v9.9.9", newDigest="sha256:" + "f" * 64)
        rendered = replacement
        for key, value in values.items():
            rendered = rendered.replace("{{{" + key + "}}}", value)
        return source[: match.start()] + rendered + source[match.end() :]

    assert replace("image: grafana/alloy:v1.0.0@sha256:" + "a" * 64) == (
        "image: grafana/alloy:v9.9.9@sha256:" + "f" * 64
    )
    assert replace("image: ${ALLOY_IMAGE:-grafana/alloy:v1.0.0@sha256:" + "a" * 64 + "}") == (
        "image: ${ALLOY_IMAGE:-grafana/alloy:v9.9.9@sha256:" + "f" * 64 + "}"
    )
    assert (
        _image_match(
            manager,
            "image: ${ALLOY_IMAGE-grafana/alloy:v1.0.0@sha256:" + "a" * 64 + "}",
        )
        is None
    )


def test_phlo_owned_images_are_explicitly_disabled_and_never_automerged() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    manager = _manager()
    rules = config["packageRules"]
    disabled = [
        rule
        for rule in rules
        if rule.get("matchManagers") == ["custom.regex"]
        and rule.get("matchPackageNames") == ["ghcr.io/phlohouse/phlo-*"]
    ]
    review_required = [
        rule
        for rule in rules
        if rule.get("matchManagers") == ["custom.regex"] and rule.get("enabled") is not False
    ]
    assert disabled == [
        {
            "description": "Do not update Phlo-owned published images as upstream dependencies.",
            "matchManagers": ["custom.regex"],
            "matchPackageNames": ["ghcr.io/phlohouse/phlo-*"],
            "enabled": False,
        }
    ]
    assert review_required and all(rule.get("automerge") is False for rule in review_required)
    assert fnmatchcase("ghcr.io/phlohouse/phlo-api", disabled[0]["matchPackageNames"][0])
    internal_files = sorted((REPO_ROOT / "packages").glob("*/src/**/*.yaml"))
    internal_files = [
        path
        for path in internal_files
        if "ghcr.io/phlohouse/phlo-" in path.read_text(encoding="utf-8")
    ]
    assert len(internal_files) == 4
    assert all(
        _image_match(manager, path.read_text(encoding="utf-8")) is None for path in internal_files
    )
