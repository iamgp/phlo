"""Integration tests for phlo-lineage."""

import pytest

pytestmark = pytest.mark.integration


def test_lineage_event_types():
    """Test lineage event types are importable."""
    from phlo.hooks import LineageEventContext, LineageEventEmitter

    assert LineageEventContext is not None
    assert LineageEventEmitter is not None


def test_lineage_emitter_creation():
    """Test LineageEventEmitter can be created."""
    from phlo.hooks import LineageEventContext, LineageEventEmitter

    context = LineageEventContext(tags={"test": "true"})
    emitter = LineageEventEmitter(context)
    assert emitter is not None


def test_lineage_edge_emission():
    """Test lineage edge emission works."""
    from phlo.hooks import LineageEventContext, LineageEventEmitter

    context = LineageEventContext(tags={"test": "true"})
    emitter = LineageEventEmitter(context)

    # Should not raise
    emitter.emit_edges(
        edges=[("source_a", "target_b")],
        asset_keys=["target_b"],
        metadata={"test": True}
    )
