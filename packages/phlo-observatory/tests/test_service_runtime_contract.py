"""Runtime contract checks for observatory service packaging."""

from importlib import resources


def test_observatory_service_mounts_docker_socket() -> None:
    """Service definition should expose Docker socket to observatory container."""
    service_yaml = resources.files("phlo_observatory").joinpath("service.yaml").read_text()
    assert "/var/run/docker.sock:/var/run/docker.sock" in service_yaml


def test_observatory_dockerfile_installs_docker_cli() -> None:
    """Container image should include docker CLI for service status discovery."""
    dockerfile = resources.files("phlo_observatory").joinpath("Dockerfile").read_text()
    assert "apk add --no-cache docker-cli" in dockerfile
