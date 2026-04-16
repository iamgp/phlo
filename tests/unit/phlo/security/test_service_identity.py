"""Tests for service-to-service identity."""

from __future__ import annotations

import time

import pytest

from phlo.security.service_identity import (
    PHLO_CORRELATION_HEADER,
    PHLO_INITIATOR_HEADER,
    PHLO_SERVICE_SECRET_ENV,
    build_service_headers,
    create_service_token,
    validate_service_token,
)


class TestCreateServiceToken:
    def test_creates_valid_token(self, monkeypatch):
        monkeypatch.setenv(PHLO_SERVICE_SECRET_ENV, "test-secret-key")
        token = create_service_token("phlo-api")
        parts = token.split(":", 2)
        assert len(parts) == 3
        assert parts[0] == "phlo-api"

    def test_raises_without_secret(self, monkeypatch):
        monkeypatch.delenv(PHLO_SERVICE_SECRET_ENV, raising=False)
        with pytest.raises(RuntimeError, match=PHLO_SERVICE_SECRET_ENV):
            create_service_token("phlo-api")

    def test_different_services_different_tokens(self, monkeypatch):
        monkeypatch.setenv(PHLO_SERVICE_SECRET_ENV, "test-secret-key")
        t1 = create_service_token("phlo-api")
        t2 = create_service_token("dagster")
        assert t1 != t2


class TestValidateServiceToken:
    def test_validates_fresh_token(self, monkeypatch):
        monkeypatch.setenv(PHLO_SERVICE_SECRET_ENV, "test-secret-key")
        token = create_service_token("phlo-api")
        result = validate_service_token(token)
        assert result == "phlo-api"

    def test_rejects_expired_token(self, monkeypatch):
        monkeypatch.setenv(PHLO_SERVICE_SECRET_ENV, "test-secret-key")
        # Manually craft an expired token
        old_timestamp = str(int(time.time()) - 600)
        import hashlib
        import hmac

        message = f"phlo-api:{old_timestamp}"
        sig = hmac.new(b"test-secret-key", message.encode(), hashlib.sha256).hexdigest()
        expired_token = f"phlo-api:{old_timestamp}:{sig}"
        assert validate_service_token(expired_token) is None

    def test_rejects_wrong_hmac(self, monkeypatch):
        monkeypatch.setenv(PHLO_SERVICE_SECRET_ENV, "test-secret-key")
        token = create_service_token("phlo-api")
        parts = token.split(":", 2)
        tampered = f"{parts[0]}:{parts[1]}:{'a' * 64}"
        assert validate_service_token(tampered) is None

    def test_rejects_malformed_token(self, monkeypatch):
        monkeypatch.setenv(PHLO_SERVICE_SECRET_ENV, "test-secret-key")
        assert validate_service_token("not-a-valid-token") is None
        assert validate_service_token("") is None
        assert validate_service_token("a:b") is None

    def test_rejects_non_numeric_timestamp(self, monkeypatch):
        monkeypatch.setenv(PHLO_SERVICE_SECRET_ENV, "test-secret-key")
        assert validate_service_token("phlo-api:not-a-number:abc") is None

    def test_returns_none_without_secret(self, monkeypatch):
        monkeypatch.delenv(PHLO_SERVICE_SECRET_ENV, raising=False)
        assert validate_service_token("phlo-api:123:abc") is None

    def test_custom_max_age(self, monkeypatch):
        monkeypatch.setenv(PHLO_SERVICE_SECRET_ENV, "test-secret-key")
        token = create_service_token("phlo-api")
        # Valid with large max_age
        assert validate_service_token(token, max_age_seconds=3600) == "phlo-api"
        # Craft a 10-second-old token, validate with 5-second max_age
        import hashlib
        import hmac

        old_ts = str(int(time.time()) - 10)
        message = f"phlo-api:{old_ts}"
        sig = hmac.new(b"test-secret-key", message.encode(), hashlib.sha256).hexdigest()
        old_token = f"phlo-api:{old_ts}:{sig}"
        assert validate_service_token(old_token, max_age_seconds=5) is None
        assert validate_service_token(old_token, max_age_seconds=30) == "phlo-api"


class TestBuildServiceHeaders:
    def test_basic_headers(self, monkeypatch):
        monkeypatch.setenv(PHLO_SERVICE_SECRET_ENV, "test-secret-key")
        headers = build_service_headers("phlo-api")
        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer phlo-api:")
        assert PHLO_INITIATOR_HEADER not in headers
        assert PHLO_CORRELATION_HEADER not in headers

    def test_with_initiator(self, monkeypatch):
        monkeypatch.setenv(PHLO_SERVICE_SECRET_ENV, "test-secret-key")
        headers = build_service_headers("phlo-api", initiator="alice@example.com")
        assert headers[PHLO_INITIATOR_HEADER] == "alice@example.com"

    def test_with_correlation_id(self, monkeypatch):
        monkeypatch.setenv(PHLO_SERVICE_SECRET_ENV, "test-secret-key")
        headers = build_service_headers("phlo-api", correlation_id="req-123")
        assert headers[PHLO_CORRELATION_HEADER] == "req-123"

    def test_with_all_fields(self, monkeypatch):
        monkeypatch.setenv(PHLO_SERVICE_SECRET_ENV, "test-secret-key")
        headers = build_service_headers(
            "phlo-api", initiator="alice@co.com", correlation_id="req-456"
        )
        assert headers["Authorization"].startswith("Bearer phlo-api:")
        assert headers[PHLO_INITIATOR_HEADER] == "alice@co.com"
        assert headers[PHLO_CORRELATION_HEADER] == "req-456"
