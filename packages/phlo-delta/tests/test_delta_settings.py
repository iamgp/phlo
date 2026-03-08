"""Tests for Delta Lake settings alias handling."""

from phlo_delta.settings import DeltaSettings


def test_delta_settings_use_standard_aws_aliases(monkeypatch) -> None:
    """Delta settings should honor the shared AWS env vars exposed in services."""
    monkeypatch.setenv("AWS_S3_ENDPOINT", "http://minio:9000")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "example-key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "example-secret")
    monkeypatch.setenv("AWS_REGION", "eu-west-2")

    settings = DeltaSettings()

    assert settings.delta_s3_endpoint == "http://minio:9000"
    assert settings.delta_s3_access_key == "example-key"
    assert settings.delta_s3_secret_key == "example-secret"
    assert settings.delta_s3_region == "eu-west-2"
