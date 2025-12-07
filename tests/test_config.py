"""Tests for Config Module.

This module contains unit and integration tests for the phlo.config module.
Tests cover configuration loading, validation, computed fields, caching, and connection strings.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from phlo.config import Settings, _get_config


class TestConfigUnitTests:
    """Unit tests for configuration loading and validation."""

    def test_config_loads_environment_variables_correctly(self):
        """Test that config loads environment variables correctly."""
        # Test with mocked environment variables
        env_vars = {
            "POSTGRES_PASSWORD": "test_password",
            "MINIO_ROOT_PASSWORD": "minio_password",
            "SUPERSET_ADMIN_PASSWORD": "superset_password",
            "POSTGRES_HOST": "test_host",
            "POSTGRES_PORT": "5433",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            test_config = Settings()

            assert test_config.postgres_password == "test_password"
            assert test_config.minio_root_password == "minio_password"
            assert test_config.superset_admin_password == "superset_password"
            assert test_config.postgres_host == "test_host"
            assert test_config.postgres_port == 5433

    def test_config_validates_required_fields_and_raises_errors_for_missing_ones(self):
        """Test that config validates required fields and raises errors for missing ones."""
        from pydantic import ValidationError
        from pydantic_settings import SettingsConfigDict

        # Since Settings loads from .env file, we need to patch the model_config to not load from file
        # and ensure no env vars are set

        # Test missing required fields when no .env file and no env vars
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(Settings, 'model_config', SettingsConfigDict(env_file=None, case_sensitive=False, extra="ignore")):
                with pytest.raises(ValidationError):
                    Settings()

        # Note: In practice, the config loads from .env file, so these fields have effective defaults.
        # This test verifies that if no .env file and no env vars, validation fails.

    def test_computed_fields_are_calculated_properly(self):
        """Test that computed fields are calculated properly."""
        env_vars = {
            "POSTGRES_PASSWORD": "test_password",
            "MINIO_ROOT_PASSWORD": "minio_password",
            "SUPERSET_ADMIN_PASSWORD": "superset_password",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            test_config = Settings()

            # Test dbt paths (assuming local environment)
            assert test_config.dbt_project_dir == "transforms/dbt"
            assert test_config.dbt_profiles_dir == "transforms/dbt/profiles"

            # Test computed properties
            assert test_config.minio_endpoint == f"{test_config.minio_host}:{test_config.minio_api_port}"
            assert test_config.nessie_uri == f"http://{test_config.nessie_host}:{test_config.nessie_port}/api"
            assert test_config.trino_connection_string == f"trino://{test_config.trino_host}:{test_config.trino_port}/{test_config.trino_catalog}"

            # Test postgres connection string
            expected_pg_conn = f"postgresql://{test_config.postgres_user}:{test_config.postgres_password}@{test_config.postgres_host}:{test_config.postgres_port}/{test_config.postgres_db}"
            assert test_config.get_postgres_connection_string() == expected_pg_conn

            # Test postgres connection string without db
            expected_pg_conn_no_db = f"postgresql://{test_config.postgres_user}:{test_config.postgres_password}@{test_config.postgres_host}:{test_config.postgres_port}"
            assert test_config.get_postgres_connection_string(include_db=False) == expected_pg_conn_no_db

    def test_computed_fields_container_environment(self):
        """Test computed fields can be overridden via environment variables."""
        # Simulate container environment by setting DBT_PROJECT_DIR env var
        env_vars = {
            "POSTGRES_PASSWORD": "test_password",
            "MINIO_ROOT_PASSWORD": "minio_password",
            "SUPERSET_ADMIN_PASSWORD": "superset_password",
            "DBT_PROJECT_DIR": "/dbt",  # Container path override
        }

        with patch.dict(os.environ, env_vars, clear=True):
            test_config = Settings()

            assert test_config.dbt_project_dir == "/dbt"
            assert test_config.dbt_profiles_dir == "/dbt/profiles"

    def test_config_handles_caching_and_returns_same_instance(self):
        """Test that config handles caching and returns the same instance."""
        env_vars = {
            "POSTGRES_PASSWORD": "test_password",
            "MINIO_ROOT_PASSWORD": "minio_password",
            "SUPERSET_ADMIN_PASSWORD": "superset_password",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            # Clear cache first
            _get_config.cache_clear()

            config1 = _get_config()
            config2 = _get_config()

            # Should be the same instance due to lru_cache
            assert config1 is config2
            assert id(config1) == id(config2)

    def test_config_generates_correct_pyiceberg_catalog_config(self):
        """Test that config generates correct PyIceberg catalog config."""
        env_vars = {
            "POSTGRES_PASSWORD": "test_password",
            "MINIO_ROOT_PASSWORD": "minio_password",
            "SUPERSET_ADMIN_PASSWORD": "superset_password",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            test_config = Settings()

            catalog_config = test_config.get_pyiceberg_catalog_config("main")

            expected_config = {
                "type": "rest",
                "uri": f"{test_config.nessie_iceberg_rest_uri}/main",
                "warehouse": test_config.iceberg_warehouse_path,
                "s3.endpoint": f"http://{test_config.minio_host}:{test_config.minio_api_port}",
                "s3.access-key-id": test_config.minio_root_user,
                "s3.secret-access-key": test_config.minio_root_password,
                "s3.path-style-access": "true",
                "s3.region": "us-east-1",
            }

            assert catalog_config == expected_config

            # Test with different branch
            catalog_config_dev = test_config.get_pyiceberg_catalog_config("dev")
            assert catalog_config_dev["uri"] == f"{test_config.nessie_iceberg_rest_uri}/dev"

    def test_get_iceberg_warehouse_for_branch(self):
        """Test get_iceberg_warehouse_for_branch method."""
        env_vars = {
            "POSTGRES_PASSWORD": "test_password",
            "MINIO_ROOT_PASSWORD": "minio_password",
            "SUPERSET_ADMIN_PASSWORD": "superset_password",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            test_config = Settings()

            # Should return the same warehouse path regardless of branch
            assert test_config.get_iceberg_warehouse_for_branch("main") == test_config.iceberg_warehouse_path
            assert test_config.get_iceberg_warehouse_for_branch("dev") == test_config.iceberg_warehouse_path


class TestConfigIntegrationTests:
    """Integration tests for configuration connection strings."""

    @patch('psycopg2.connect')
    def test_config_provides_valid_connection_strings_for_postgres(self, mock_connect):
        """Test that config provides valid connection strings for Postgres."""
        env_vars = {
            "POSTGRES_PASSWORD": "test_password",
            "MINIO_ROOT_PASSWORD": "minio_password",
            "SUPERSET_ADMIN_PASSWORD": "superset_password",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            test_config = Settings()

            conn_string = test_config.get_postgres_connection_string()

            # Mock successful connection
            mock_connect.return_value = MagicMock()

            # This would be the actual integration test - attempting to connect
            # For now, just verify the connection string format
            assert conn_string.startswith("postgresql://")
            assert test_config.postgres_user in conn_string
            assert test_config.postgres_host in conn_string
            assert str(test_config.postgres_port) in conn_string
            assert test_config.postgres_db in conn_string

    @patch('trino.dbapi.connect')
    def test_config_provides_valid_connection_strings_for_trino(self, mock_connect):
        """Test that config provides valid connection strings for Trino."""
        env_vars = {
            "POSTGRES_PASSWORD": "test_password",
            "MINIO_ROOT_PASSWORD": "minio_password",
            "SUPERSET_ADMIN_PASSWORD": "superset_password",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            test_config = Settings()

            conn_string = test_config.trino_connection_string

            # Mock successful connection
            mock_connect.return_value = MagicMock()

            # Verify the connection string format
            assert conn_string.startswith("trino://")
            assert test_config.trino_host in conn_string
            assert str(test_config.trino_port) in conn_string
            assert test_config.trino_catalog in conn_string
