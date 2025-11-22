"""Tests for Definitions Module.

This module contains unit and integration tests for the
phlo.definitions module, focusing on definition merging and executor selection.
"""

from unittest.mock import patch


from phlo.definitions import _default_executor, _merged_definitions, defs


class TestDefinitionsUnitTests:
    """Unit tests for definition merging and executor selection."""

    @patch('phlo.definitions.config')
    def test_executor_selection_works_for_different_platforms(self, mock_config):
        """Test that executor selection works for different platforms."""
        mock_config.cascade_force_in_process_executor = False
        mock_config.cascade_force_multiprocess_executor = False

        # Test macOS (Darwin) - should use in-process
        with patch('platform.system', return_value='Darwin'):
            executor = _default_executor()
            assert executor is not None
            assert executor.name == 'in_process'

        # Test Linux - should use multiprocess
        with patch('platform.system', return_value='Linux'):
            executor = _default_executor()
            assert executor is not None
            assert executor.name == 'multiprocess'

        # Test Windows - should use multiprocess
        with patch('platform.system', return_value='Windows'):
            executor = _default_executor()
            assert executor is not None
            assert executor.name == 'multiprocess'

    @patch('phlo.definitions.config')
    def test_executor_selection_respects_force_flags(self, mock_config):
        """Test that executor selection respects force flags."""
        # Test force in-process
        mock_config.cascade_force_in_process_executor = True
        mock_config.cascade_force_multiprocess_executor = False

        executor = _default_executor()
        assert executor is not None
        assert executor.name == 'in_process'

        # Test force multiprocess
        mock_config.cascade_force_in_process_executor = False
        mock_config.cascade_force_multiprocess_executor = True

        executor = _default_executor()
        assert executor is not None
        assert executor.name == 'multiprocess'

    @patch('phlo.definitions.build_resource_defs')
    @patch('phlo.definitions.build_ingestion_defs')
    @patch('phlo.definitions.build_transform_defs')
    @patch('phlo.definitions.build_publishing_defs')
    @patch('phlo.definitions.build_quality_defs')
    @patch('phlo.definitions.build_nessie_defs')
    @patch('phlo.definitions.build_schedule_defs')
    @patch('phlo.definitions.build_sensor_defs')
    @patch('phlo.definitions.build_job_defs')
    @patch('phlo.definitions.build_workflow_defs')
    @patch('phlo.definitions._default_executor')
    def test_definitions_merges_all_component_defs_correctly(self, mock_executor, mock_workflow_defs, mock_job_defs, mock_sensor_defs, mock_schedule_defs, mock_nessie_defs, mock_quality_defs, mock_publishing_defs, mock_transform_defs, mock_ingestion_defs, mock_resource_defs):
        """Test that definitions merges all component defs correctly."""
        # Mock all the build functions to return empty definitions
        from dagster import Definitions
        empty_defs = Definitions(
            assets=[],
            asset_checks=[],
            schedules=[],
            sensors=[],
            resources={},
            jobs=[],
        )

        mock_resource_defs.return_value = empty_defs
        mock_ingestion_defs.return_value = empty_defs
        mock_transform_defs.return_value = empty_defs
        mock_publishing_defs.return_value = empty_defs
        mock_quality_defs.return_value = empty_defs
        mock_nessie_defs.return_value = empty_defs
        mock_schedule_defs.return_value = empty_defs
        mock_sensor_defs.return_value = empty_defs
        mock_job_defs.return_value = empty_defs
        mock_workflow_defs.return_value = empty_defs

        mock_executor.return_value = None

        # Execute merge
        result = _merged_definitions()

        # Verify all build functions were called
        mock_resource_defs.assert_called_once()
        mock_ingestion_defs.assert_called_once()
        mock_transform_defs.assert_called_once()
        mock_publishing_defs.assert_called_once()
        mock_quality_defs.assert_called_once()
        mock_nessie_defs.assert_called_once()
        mock_schedule_defs.assert_called_once()
        mock_sensor_defs.assert_called_once()
        mock_job_defs.assert_called_once()
        mock_workflow_defs.assert_called_once()

        # Verify result is a Definitions object
        assert hasattr(result, 'assets')
        assert hasattr(result, 'asset_checks')
        assert hasattr(result, 'schedules')
        assert hasattr(result, 'sensors')
        assert hasattr(result, 'resources')
        assert hasattr(result, 'jobs')


class TestDefinitionsIntegrationTests:
    """Integration tests for definition merging."""

    def test_merged_definitions_include_all_assets_checks_jobs_schedules_sensors(self):
        """Test that merged definitions include all assets, checks, jobs, schedules, sensors."""
        # This test verifies that the global defs object contains all expected components
        # We can't easily mock all the build functions for the global defs, so we test
        # the structure instead

        # Verify defs is a Definitions object
        assert hasattr(defs, 'assets')
        assert hasattr(defs, 'asset_checks')
        assert hasattr(defs, 'schedules')
        assert hasattr(defs, 'sensors')
        assert hasattr(defs, 'resources')
        assert hasattr(defs, 'jobs')

        # Verify assets exist (at minimum the ones we know about)
        asset_keys = []
        if defs.assets:
            for asset in defs.assets:
                if hasattr(asset, 'keys'):
                    # Multi-asset definition
                    asset_keys.extend(asset.keys)
                else:
                    # Single asset or try key
                    try:
                        asset_keys.append(asset.key)
                    except:
                        # Skip assets that don't have accessible keys
                        continue
        # Should contain entries asset and dbt assets
        assert any('entries' in str(key) for key in asset_keys)

        # Verify resources exist
        assert defs.resources is not None
        assert 'trino' in defs.resources
        assert 'iceberg' in defs.resources
        assert 'dbt' in defs.resources

        # Verify schedules exist
        schedule_names = [schedule.name for schedule in defs.schedules] if defs.schedules else []
        assert 'daily_ingestion_fallback' in schedule_names

        # Verify sensors exist
        sensor_names = [sensor.name for sensor in defs.sensors] if defs.sensors else []
        assert len(sensor_names) >= 1  # Should have at least the transform sensor

        # Verify asset checks exist
        assert len(defs.asset_checks) >= 1  # Should have quality checks

        # Verify jobs exist
        job_names = [job.name for job in defs.jobs] if defs.jobs else []
        assert 'ingest_raw_data' in job_names
        assert 'transform_dbt_models' in job_names
