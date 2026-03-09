"""Tests for Sling executor."""

from phlo_sling.registry import ReplicationConfig


def test_replication_config_asset_key():
    """Validate asset_key format."""
    config = ReplicationConfig(
        stream_name="public.users",
        table_name="users",
        source_conn="MY_PG",
    )
    assert config.asset_key == "sling_users"
