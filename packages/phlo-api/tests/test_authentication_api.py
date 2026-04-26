"""Tests for phlo-api authentication helpers."""

from __future__ import annotations

import pytest
from pathlib import Path

from phlo.capabilities import AuthenticationProviderSpec, clear_capabilities
from phlo.capabilities.registry import register_authentication_provider
from phlo.infrastructure.config import clear_config_cache
from phlo_api.api.authentication import get_authentication_provider


def teardown_function() -> None:
    clear_capabilities()
    clear_config_cache()


def _write_phlo_config(tmp_path: Path, content: str) -> None:
    (tmp_path / "phlo.yaml").write_text(content)


class _DummyAuthenticationProvider:
    pass


def test_get_authentication_provider_uses_phlo_yaml(monkeypatch, tmp_path: Path) -> None:
    provider = _DummyAuthenticationProvider()
    register_authentication_provider(AuthenticationProviderSpec(name="proxy", provider=provider))

    _write_phlo_config(
        tmp_path,
        """
authentication:
  provider: proxy
""".lstrip(),
    )
    monkeypatch.delenv("PHLO_AUTHENTICATION_PROVIDER", raising=False)
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    clear_config_cache()

    assert get_authentication_provider() is provider


def test_env_authentication_provider_overrides_phlo_yaml(monkeypatch, tmp_path: Path) -> None:
    proxy_provider = _DummyAuthenticationProvider()
    static_provider = _DummyAuthenticationProvider()
    register_authentication_provider(
        AuthenticationProviderSpec(name="proxy", provider=proxy_provider)
    )
    register_authentication_provider(
        AuthenticationProviderSpec(name="static", provider=static_provider)
    )

    _write_phlo_config(
        tmp_path,
        """
authentication:
  provider: proxy
""".lstrip(),
    )
    monkeypatch.setenv("PHLO_AUTHENTICATION_PROVIDER", "static")
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    clear_config_cache()

    assert get_authentication_provider() is static_provider


def test_empty_env_authentication_provider_falls_back_to_phlo_yaml(
    monkeypatch, tmp_path: Path
) -> None:
    provider = _DummyAuthenticationProvider()
    register_authentication_provider(AuthenticationProviderSpec(name="proxy", provider=provider))

    _write_phlo_config(
        tmp_path,
        """
authentication:
  provider: proxy
""".lstrip(),
    )
    monkeypatch.setenv("PHLO_AUTHENTICATION_PROVIDER", "")
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(tmp_path))
    clear_config_cache()

    assert get_authentication_provider() is provider


def test_phlo_api_has_forward_auth_middleware() -> None:
    """Verify phlo-api declares forwardAuth middleware for oauth2-proxy.

    The middleware is defined in service-auth.yaml which is conditionally
    included when the proxy profile is active.
    """
    import yaml
    from importlib.resources import files

    package_root = files("phlo_api")
    auth_defn_path = package_root / "service-auth.yaml"

    if not auth_defn_path.exists():
        pytest.skip("service-auth.yaml not found - oauth2-proxy integration not configured")

    with open(auth_defn_path) as f:
        auth_defn = yaml.safe_load(f)

    auth_labels = auth_defn.get("compose", {}).get("labels", {})

    assert "traefik.http.routers.api.middlewares" in auth_labels
    assert auth_labels["traefik.http.routers.api.middlewares"] == "phlo-api-auth@docker"
    assert "traefik.http.middlewares.phlo-api-auth.forwardauth.address" in auth_labels
    assert (
        "/oauth2/auth" in auth_labels["traefik.http.middlewares.phlo-api-auth.forwardauth.address"]
    )
    assert (
        "oauth2-proxy" in auth_labels["traefik.http.middlewares.phlo-api-auth.forwardauth.address"]
    )
    assert (
        auth_labels["traefik.http.middlewares.phlo-api-auth.forwardauth.trustForwardHeader"]
        == "true"
    )
    assert (
        "X-Forwarded-User"
        in auth_labels["traefik.http.middlewares.phlo-api-auth.forwardauth.authResponseHeaders"]
    )
    assert (
        "X-Forwarded-Email"
        in auth_labels["traefik.http.middlewares.phlo-api-auth.forwardauth.authResponseHeaders"]
    )
    assert (
        "X-Forwarded-Groups"
        in auth_labels["traefik.http.middlewares.phlo-api-auth.forwardauth.authResponseHeaders"]
    )


def test_phlo_api_service_passes_clickstack_query_env() -> None:
    import yaml
    from importlib.resources import files

    service_defn_path = files("phlo_api") / "service.yaml"

    with open(service_defn_path) as f:
        service_defn = yaml.safe_load(f)

    compose_env = service_defn["compose"]["environment"]
    dev_env = service_defn["dev"]["environment"]

    for env in (compose_env, dev_env):
        assert env["CLICKSTACK_QUERY_URL"] == "${CLICKSTACK_QUERY_URL:-}"
        assert env["CLICKSTACK_QUERY_USER"] == "${CLICKSTACK_QUERY_USER:-}"
        assert env["CLICKSTACK_QUERY_PASSWORD"] == "${CLICKSTACK_QUERY_PASSWORD:-}"
