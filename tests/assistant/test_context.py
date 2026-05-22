from phlo.assistant import AssistantContextBundle, build_incident_context


def test_build_incident_context_redacts_secret_like_values() -> None:
    bundle = build_incident_context(
        title="Quality failure",
        facts={
            "table": "silver.orders",
            "error": "token=abc123 failed not_null(order_id)",
            "dsn": "postgresql://user:pass@localhost/db",
        },
        suggested_actions=["inspect_quality_check", "open_lineage"],
    )

    payload = bundle.to_read_model()

    assert payload["title"] == "Quality failure"
    assert payload["facts"]["error"] == "token=<redacted> failed not_null(order_id)"
    assert payload["facts"]["dsn"] == "<redacted-dsn>"
    assert payload["suggested_actions"] == ["inspect_quality_check", "open_lineage"]


def test_read_model_redacts_token_case_insensitively() -> None:
    bundle = AssistantContextBundle(
        title="Incident",
        facts={"error": "Token=abc123 failed"},
        suggested_actions=(),
    )

    payload = bundle.to_read_model()

    assert payload["facts"]["error"] == "Token=<redacted> failed"


def test_assistant_context_to_prompt_is_deterministic() -> None:
    bundle = AssistantContextBundle(
        title="Quality failure",
        facts={"table": "silver.orders", "check": "not_null(order_id)"},
        suggested_actions=("inspect_quality_check",),
    )

    assert bundle.to_prompt() == (
        "Incident: Quality failure\n"
        "Facts:\n"
        "- check: not_null(order_id)\n"
        "- table: silver.orders\n"
        "Suggested actions:\n"
        "- inspect_quality_check"
    )


def test_assistant_context_to_prompt_redacts_secret_like_values() -> None:
    bundle = AssistantContextBundle(
        title="Incident",
        facts={
            "error": "TOKEN=abc123",
            "dsn": "postgresql://user:pass@localhost/db",
        },
        suggested_actions=(),
    )

    prompt = bundle.to_prompt()

    assert "TOKEN=<redacted>" in prompt
    assert "<redacted-dsn>" in prompt
    assert "abc123" not in prompt
    assert "user:pass" not in prompt
