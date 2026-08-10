"""Contracts for generated service image publication and remote CI scanning."""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import yaml

from phlo.plugins.compose.generator import ComposeGenerator
from phlo.plugins.discovery import ServiceDiscovery

REPO_ROOT = Path(__file__).resolve().parents[2]
MATRIX_SPEC = importlib.util.spec_from_file_location(
    "generated_image_matrix", REPO_ROOT / "scripts" / "generated_image_matrix.py"
)
assert MATRIX_SPEC and MATRIX_SPEC.loader
GENERATED_IMAGE_MATRIX = importlib.util.module_from_spec(MATRIX_SPEC)
sys.modules["generated_image_matrix"] = GENERATED_IMAGE_MATRIX
MATRIX_SPEC.loader.exec_module(GENERATED_IMAGE_MATRIX)


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


def test_generated_prometheus_and_trino_use_upstream_images_and_are_not_published(
    tmp_path: Path, monkeypatch
) -> None:
    discovery = ServiceDiscovery()
    services = [
        service
        for name in ("prometheus", "trino", "postgres")
        if (service := discovery.get_service(name)) is not None
    ]
    generated_root = tmp_path / ".phlo"
    generated_root.mkdir()
    compose = yaml.safe_load(
        ComposeGenerator(discovery).generate_compose(services, output_dir=generated_root)
    )

    assert compose["services"]["prometheus"]["image"] == (
        "${PROMETHEUS_IMAGE:-prom/prometheus:v3.13.1@"
        "sha256:3c42b892cf723fa54d2f262c37a0e1f80aa8c8ddb1da7b9b0df9455a35a7f893}"
    )
    assert compose["services"]["trino"]["image"] == (
        "trinodb/trino:483@sha256:db58cc93e593a2706553745f276bb119c9810e69918be56ecde088ba7ccb0534"
    )
    assert "build" not in compose["services"]["prometheus"]
    assert "build" not in compose["services"]["trino"]

    monkeypatch.chdir(generated_root)
    targets = GENERATED_IMAGE_MATRIX.publication_matrix(compose, tmp_path)["include"]
    published_services = {target["service"] for target in targets}

    assert "prometheus" not in published_services
    assert "trino" not in published_services


def test_publication_workflow_publishes_attested_images_after_digest_scans() -> None:
    workflow = (REPO_ROOT / ".github/workflows/build-core-services.yml").read_text(encoding="utf-8")

    assert "pull_request:" not in workflow
    assert "\n  push:" in workflow
    assert "fetch-depth: 0" in workflow
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
    assert "name: digest-${{ matrix.target.service }}-amd64" in workflow
    assert "name: digest-${{ matrix.target.service }}-arm64" in workflow
    assert "pattern: digest-${{ matrix.target.service }}-*" not in workflow
    assert "docker buildx imagetools create" in workflow
    assert "timeout-minutes: 45" in workflow
    assert "max-parallel: 8" in workflow
    assert "org.opencontainers.image.source=https://github.com/${{ github.repository }}" in workflow
    assert "Scan immutable architecture digest" in workflow
    assert "apply-policy" in workflow
    assert '-v "$PWD:/work" -w /work' in workflow
    assert (
        '"/work/security-reports/${{ matrix.target.service }}-${{ matrix.architecture.name }}.json"'
        in workflow
    )
    assert "PLATFORM: ${{ matrix.architecture.platform }}" in workflow
    assert 'image --platform "$PLATFORM"' in workflow


def test_container_security_replaces_legacy_remote_image_scan() -> None:
    workflow = (REPO_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    container_workflow = (REPO_ROOT / ".github/workflows/container-security.yml").read_text(
        encoding="utf-8"
    )

    assert "generated-container-checks" not in workflow
    assert "--allow-vulnerable-image" not in workflow
    assert "--remote-images" not in workflow
    assert "generated-files" in container_workflow
    assert "docker build" not in container_workflow
    assert "aquasec/trivy" not in container_workflow
