from phlo.efficiency import (
    TableEfficiencyInput,
    build_efficiency_report,
    score_table_efficiency,
)


def test_score_table_efficiency_flags_small_files() -> None:
    report = score_table_efficiency(
        TableEfficiencyInput(
            table="bronze.events",
            file_count=1200,
            total_bytes=1200 * 1024 * 1024,
            snapshot_count=8,
            latest_run_seconds=120,
        )
    )

    assert report[0].code == "small_files"
    assert report[0].severity == "warning"
    assert "average file size is 1.0 MiB" in report[0].message


def test_score_table_efficiency_flags_stale_snapshots() -> None:
    report = score_table_efficiency(
        TableEfficiencyInput(
            table="bronze.events",
            file_count=10,
            total_bytes=10 * 128 * 1024 * 1024,
            snapshot_count=250,
            latest_run_seconds=120,
        )
    )

    assert report[0].code == "snapshot_retention"
    assert report[0].recommended_action == "expire_snapshots"


def test_score_table_efficiency_allows_missing_latest_run_duration() -> None:
    report = score_table_efficiency(
        TableEfficiencyInput(
            table="bronze.events",
            file_count=10,
            total_bytes=10 * 128 * 1024 * 1024,
            snapshot_count=8,
            latest_run_seconds=None,
        )
    )

    assert report == []


def test_efficiency_finding_serializes_for_observatory() -> None:
    report = score_table_efficiency(
        TableEfficiencyInput(
            table="bronze.events",
            file_count=1200,
            total_bytes=1200 * 1024 * 1024,
            snapshot_count=8,
            latest_run_seconds=120,
        )
    )

    assert report[0].to_read_model() == {
        "table": "bronze.events",
        "code": "small_files",
        "severity": "warning",
        "message": "bronze.events average file size is 1.0 MiB across 1200 files",
        "recommended_action": "compact_files",
        "metrics": {"average_file_mib": 1.0, "file_count": 1200},
    }


def test_build_efficiency_report_serializes_findings() -> None:
    report = build_efficiency_report(
        [
            TableEfficiencyInput(
                table="bronze.events",
                file_count=1200,
                total_bytes=1200 * 1024 * 1024,
                snapshot_count=8,
            )
        ]
    )

    assert report["summary"] == {"tables_scored": 1, "finding_count": 1}
    assert report["findings"][0]["code"] == "small_files"
