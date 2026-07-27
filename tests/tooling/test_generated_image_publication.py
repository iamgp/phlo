"""Contracts for generated service image publication and remote CI scanning."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


def _published_image(raw_image: str) -> str:
    match = re.fullmatch(r"\$\{[^:}]+:-(.+)}", raw_image)
    return match.group(1) if match else raw_image


def test_every_generated_build_uses_a_versioned_ghcr_image() -> None:
    build_definitions: list[tuple[Path, str]] = []
    for service_file in sorted((REPO_ROOT / "packages").glob("*/src/*/*.yaml")):
        service = yaml.safe_load(service_file.read_text(encoding="utf-8"))
        if not isinstance(service, dict) or not service.get("build"):
            continue
        image = service.get("image")
        assert isinstance(image, str), f"{service_file} has a build but no image"
        build_definitions.append((service_file, _published_image(image)))

    assert build_definitions
    for service_file, image in build_definitions:
        assert image.startswith("ghcr.io/phlohouse/phlo-"), service_file
        assert ":" in image.rsplit("/", 1)[-1], service_file
        assert not image.endswith(":latest"), service_file


def test_publication_workflow_publishes_only_on_release_or_manual_dispatch() -> None:
    workflow = (REPO_ROOT / ".github/workflows/build-core-services.yml").read_text(encoding="utf-8")

    assert "pull_request:" not in workflow
    assert "\n  push:" not in workflow
    assert "workflow_dispatch:" in workflow
    assert "release:" in workflow
    assert "PUBLISH_SERVICES" in workflow
    assert "packages: write" in workflow
    assert "docker/build-push-action@" in workflow
    assert "ubuntu-24.04-arm" in workflow
    assert "platform: linux/amd64" in workflow
    assert "platform: linux/arm64" in workflow
    assert "setup-qemu-action@" not in workflow
    assert "push-by-digest=true" in workflow
    assert "name=${{ steps.image.outputs.repository }},push-by-digest=true" in workflow
    assert "name=${{ matrix.target.image }},push-by-digest=true" not in workflow
    assert "if: always() && needs.prepare.result == 'success'" in workflow
    assert "docker buildx imagetools create" in workflow
    assert "timeout-minutes: 45" in workflow
    assert "max-parallel: 8" in workflow
    assert "org.opencontainers.image.source=https://github.com/${{ github.repository }}" in workflow


def test_ci_scans_published_images_remotely() -> None:
    workflow = (REPO_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    command = re.search(r"phlo --no-color plugin check --containers[^\n]*", workflow)
    assert command
    assert "--remote-images" in command.group(0)
