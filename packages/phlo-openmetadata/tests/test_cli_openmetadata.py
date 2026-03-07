"""CLI tests for OpenMetadata commands."""

from unittest.mock import Mock, patch

from click.testing import CliRunner

from phlo_openmetadata.cli_openmetadata import openmetadata


def test_sync_uses_catalog_scanner_capability():
    """Sync command resolves its scanner through the capability helper."""
    runner = CliRunner()
    scanner = Mock()
    client = Mock()
    client.health_check.return_value = True

    with (
        patch("phlo_openmetadata.cli_openmetadata.OpenMetadataClient", return_value=client),
        patch("phlo_openmetadata.cli_openmetadata.resolve_catalog_scanner", return_value=scanner),
        patch(
            "phlo_openmetadata.cli_openmetadata.get_settings",
            return_value=Mock(openmetadata_catalog_scanner="catalog-a"),
        ),
        patch(
            "phlo_openmetadata.cli_openmetadata.sync_nessie_tables_to_openmetadata",
            return_value={"created": 2, "failed": 0},
        ) as sync_mock,
    ):
        result = runner.invoke(openmetadata, ["sync", "--no-dbt"])

    assert result.exit_code == 0
    sync_mock.assert_called_once()
    assert sync_mock.call_args.args[0] is scanner


def test_sync_uses_configured_catalog_scanner_name():
    """Sync command passes the configured capability name into resolution."""
    runner = CliRunner()
    client = Mock()
    client.health_check.return_value = True

    with (
        patch("phlo_openmetadata.cli_openmetadata.OpenMetadataClient", return_value=client),
        patch(
            "phlo_openmetadata.cli_openmetadata.get_settings",
            return_value=Mock(openmetadata_catalog_scanner="catalog-a"),
        ),
        patch(
            "phlo_openmetadata.cli_openmetadata.resolve_catalog_scanner",
            return_value=Mock(),
        ) as resolve_mock,
        patch(
            "phlo_openmetadata.cli_openmetadata.sync_nessie_tables_to_openmetadata",
            return_value={"created": 0, "failed": 0},
        ),
    ):
        result = runner.invoke(openmetadata, ["sync", "--no-dbt"])

    assert result.exit_code == 0
    resolve_mock.assert_called_once_with("catalog-a")


def test_sync_fails_cleanly_when_catalog_scanner_missing():
    """Sync command exits with a clear error when no scanner capability is available."""
    runner = CliRunner()
    client = Mock()
    client.health_check.return_value = True

    with (
        patch("phlo_openmetadata.cli_openmetadata.OpenMetadataClient", return_value=client),
        patch(
            "phlo_openmetadata.cli_openmetadata.get_settings",
            return_value=Mock(openmetadata_catalog_scanner=None),
        ),
        patch(
            "phlo_openmetadata.cli_openmetadata.resolve_catalog_scanner",
            side_effect=RuntimeError("No catalog scanner capability is available."),
        ),
    ):
        result = runner.invoke(openmetadata, ["sync", "--no-dbt"])

    assert result.exit_code == 1
    assert "No catalog scanner capability is available." in result.output
