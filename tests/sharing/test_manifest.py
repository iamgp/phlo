from phlo.governance.catalog import GovernanceCatalog
from phlo.sharing import ShareDataset, ShareManifest


def _catalog() -> GovernanceCatalog:
    return GovernanceCatalog.from_dict(
        {"version": 1, "datasets": [{"id": "gold.revenue", "owner": "finance"}]}
    )


def test_share_manifest_parses_read_only_share() -> None:
    manifest = ShareManifest.from_dict(
        {
            "version": 1,
            "share_id": "partner-revenue",
            "title": "Partner Revenue Share",
            "datasets": [{"id": "gold.revenue", "mode": "read"}],
            "recipients": [{"id": "partner-a", "type": "partner"}],
        },
        catalog=_catalog(),
    )

    assert manifest.share_id == "partner-revenue"
    assert manifest.datasets[0].id == "gold.revenue"
    assert manifest.recipients[0].id == "partner-a"


def test_share_manifest_serializes_browser_safe_payload() -> None:
    manifest = ShareManifest.from_dict(
        {
            "version": 1,
            "share_id": "partner-revenue",
            "title": "Partner Revenue Share",
            "datasets": [{"id": "gold.revenue", "mode": "read"}],
            "recipients": [{"id": "partner-a", "type": "partner"}],
        },
        catalog=_catalog(),
    )

    assert manifest.to_read_model() == {
        "version": 1,
        "share_id": "partner-revenue",
        "title": "Partner Revenue Share",
        "datasets": [{"id": "gold.revenue", "mode": "read"}],
        "recipients": [{"id": "partner-a", "type": "partner"}],
    }


def test_share_manifest_rejects_write_mode() -> None:
    try:
        ShareManifest.from_dict(
            {
                "share_id": "bad-share",
                "datasets": [{"id": "gold.revenue", "mode": "write"}],
                "recipients": [{"id": "partner-a", "type": "partner"}],
            },
            catalog=_catalog(),
        )
    except ValueError as exc:
        assert "Shares are read-only in v1: gold.revenue requested write" in str(exc)
    else:
        raise AssertionError("Expected write mode to fail")


def test_share_dataset_rejects_write_mode() -> None:
    try:
        ShareDataset(id="gold.revenue", mode="write")
    except ValueError as exc:
        assert "Shares are read-only in v1: gold.revenue requested write" in str(exc)
    else:
        raise AssertionError("Expected write mode to fail")


def test_share_manifest_rejects_unknown_dataset() -> None:
    try:
        ShareManifest.from_dict(
            {
                "share_id": "bad-share",
                "datasets": [{"id": "gold.unknown", "mode": "read"}],
                "recipients": [{"id": "partner-a", "type": "partner"}],
            },
            catalog=_catalog(),
        )
    except ValueError as exc:
        assert "Share references unknown governed dataset: gold.unknown" in str(exc)
    else:
        raise AssertionError("Expected unknown dataset to fail")
