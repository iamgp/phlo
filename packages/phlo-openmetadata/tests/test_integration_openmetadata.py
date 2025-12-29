"""Integration tests for phlo-openmetadata."""

import pytest

pytestmark = pytest.mark.integration


def test_openmetadata_client_importable():
    """Test that OpenMetadataClient can be imported."""
    from phlo_openmetadata import OpenMetadataClient

    assert OpenMetadataClient is not None


def test_openmetadata_models_importable():
    """Test that OpenMetadata models can be imported."""
    from phlo_openmetadata import (
        OpenMetadataColumn,
        OpenMetadataLineageEdge,
        OpenMetadataTable,
    )

    assert OpenMetadataColumn is not None
    assert OpenMetadataLineageEdge is not None
    assert OpenMetadataTable is not None


def test_dbt_manifest_parser_importable():
    """Test that DbtManifestParser can be imported."""
    from phlo_openmetadata import DbtManifestParser

    assert DbtManifestParser is not None
