"""Contract for the required live PostgreSQL concurrency gate."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_ci_runs_the_three_postgres_concurrency_gates_without_skips() -> None:
    workflow = (REPO_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "postgres-concurrency-gates:" in workflow
    assert "name: postgres / concurrency gates" in workflow
    assert "image: postgres:16-alpine" in workflow
    assert "PHLO_SERVICE_TOKEN_TEST_POSTGRES_DSN" in workflow
    assert "PHLO_RUN_EVIDENCE_TEST_POSTGRES_DSN" in workflow
    assert "test_postgres_nonce_store_rejects_one_of_two_simultaneous_consumers" in workflow
    assert "test_postgres_concurrent_duplicate_replay_does_not_apply_loser_run_metadata" in workflow
    assert "test_true_v2_to_v3_upgrade_is_idempotent_and_compatible_postgres" in workflow
    assert "PostgreSQL concurrency gate DSNs must be set" in workflow
    assert "PostgreSQL concurrency gates must report exactly 3 passed, 0 skipped" in workflow
