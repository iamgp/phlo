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


def test_read_model_redacts_password_like_values_and_bearer_tokens() -> None:
    bundle = AssistantContextBundle(
        title="Incident",
        facts={
            "error": "password=hunter2 failed",
            "auth": "Bearer deadbeef",
        },
        suggested_actions=(),
    )

    payload = bundle.to_read_model()

    assert payload["facts"]["error"] == "password=<redacted> failed"
    assert payload["facts"]["auth"] == "Bearer <redacted>"
    assert "hunter2" not in str(payload)
    assert "deadbeef" not in str(payload)


def test_read_model_redacts_embedded_dsns_and_compound_token_keys() -> None:
    bundle = AssistantContextBundle(
        title="Incident",
        facts={
            "connection": "connect failed: postgresql://user:pass@localhost/db timeout",
            "tokens": "access_token=abc refresh_token=def api-key=ghi",
        },
        suggested_actions=(),
    )

    payload = bundle.to_read_model()

    assert payload["facts"]["connection"] == "connect failed: <redacted-dsn> timeout"
    assert payload["facts"]["tokens"] == (
        "access_token=<redacted> refresh_token=<redacted> api-key=<redacted>"
    )
    assert "user:pass" not in str(payload)
    assert "abc" not in str(payload)
    assert "def" not in str(payload)
    assert "ghi" not in str(payload)


def test_read_model_redacts_title_and_suggested_actions() -> None:
    bundle = AssistantContextBundle(
        title="Incident token=titleSecret",
        facts={},
        suggested_actions=("rotate password=actionSecret", "notify Bearer actionBearer"),
    )

    payload = bundle.to_read_model()

    assert payload["title"] == "Incident token=<redacted>"
    assert payload["suggested_actions"] == [
        "rotate password=<redacted>",
        "notify Bearer <redacted>",
    ]
    assert "titleSecret" not in str(payload)
    assert "actionSecret" not in str(payload)
    assert "actionBearer" not in str(payload)


def test_read_model_redacts_authorization_bearer_and_quoted_secret_values() -> None:
    bundle = AssistantContextBundle(
        title="Incident",
        facts={
            "authorization_header": "Authorization Bearer deadbeef",
            "authorization_colon": "Authorization: Bearer cafebabe",
            "quoted_secret": 'password="hunter two" failed',
            "quoted_secret_colon": "api-key: 'key with spaces'",
        },
        suggested_actions=(),
    )

    payload = bundle.to_read_model()

    assert payload["facts"]["authorization_header"] == "Authorization Bearer <redacted>"
    assert payload["facts"]["authorization_colon"] == "Authorization: Bearer <redacted>"
    assert payload["facts"]["quoted_secret"] == "password=<redacted> failed"
    assert payload["facts"]["quoted_secret_colon"] == "api-key=<redacted>"
    assert "deadbeef" not in str(payload)
    assert "cafebabe" not in str(payload)
    assert "hunter two" not in str(payload)
    assert "key with spaces" not in str(payload)


def test_read_model_redacts_secret_like_fact_keys_and_preserves_collisions() -> None:
    bundle = AssistantContextBundle(
        title="Incident",
        facts={
            "token=abc123": "failed",
            "token=def456": "retry",
            "table": "silver.orders",
        },
        suggested_actions=(),
    )

    payload = bundle.to_read_model()

    assert payload["facts"] == {
        "token=<redacted>": "failed",
        "token=<redacted> (2)": "retry",
        "table": "silver.orders",
    }
    assert "abc123" not in str(payload)
    assert "def456" not in str(payload)


def test_read_model_preserves_structured_fact_values_and_redacts_nested_strings() -> None:
    bundle = AssistantContextBundle(
        title="Incident",
        facts={
            "failed_rows": 12,
            "has_failures": True,
            "checks": ["not_null(order_id)", "token=abc123"],
            "metadata": {
                "owner": "analytics",
                "password": "password=hunter2",
                "attempts": (1, 2),
            },
        },
        suggested_actions=(),
    )

    payload = bundle.to_read_model()

    assert payload["facts"] == {
        "failed_rows": 12,
        "has_failures": True,
        "checks": ["not_null(order_id)", "token=<redacted>"],
        "metadata": {
            "owner": "analytics",
            "password": "<redacted>",
            "attempts": [1, 2],
        },
    }
    assert "abc123" not in str(payload)
    assert "hunter2" not in str(payload)


def test_read_model_redacts_values_for_nested_secret_like_keys() -> None:
    bundle = AssistantContextBundle(
        title="Incident",
        facts={
            "metadata": {
                "password": "hunter2",
                "api_key": "abc123",
                "nested": {"refresh_token": "deadbeef"},
                "owner": "analytics",
            },
        },
        suggested_actions=(),
    )

    payload = bundle.to_read_model()

    assert payload["facts"] == {
        "metadata": {
            "password": "<redacted>",
            "api_key": "<redacted>",
            "nested": {"refresh_token": "<redacted>"},
            "owner": "analytics",
        },
    }
    assert "hunter2" not in str(payload)
    assert "abc123" not in str(payload)
    assert "deadbeef" not in str(payload)


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


def test_assistant_context_to_prompt_redacts_password_like_values_and_bearer_tokens() -> None:
    bundle = AssistantContextBundle(
        title="Incident",
        facts={
            "auth": "Bearer deadbeef",
            "error": "password=hunter2 failed",
        },
        suggested_actions=(),
    )

    assert bundle.to_prompt() == (
        "Incident: Incident\n"
        "Facts:\n"
        "- auth: Bearer <redacted>\n"
        "- error: password=<redacted> failed\n"
        "Suggested actions:"
    )


def test_assistant_context_to_prompt_redacts_embedded_dsns_and_compound_token_keys() -> None:
    bundle = AssistantContextBundle(
        title="Incident",
        facts={
            "connection": "connect failed: postgresql://user:pass@localhost/db timeout",
            "tokens": "access_token=abc refresh_token=def api-key=ghi",
        },
        suggested_actions=(),
    )

    assert bundle.to_prompt() == (
        "Incident: Incident\n"
        "Facts:\n"
        "- connection: connect failed: <redacted-dsn> timeout\n"
        "- tokens: access_token=<redacted> refresh_token=<redacted> api-key=<redacted>\n"
        "Suggested actions:"
    )


def test_assistant_context_to_prompt_redacts_title_and_suggested_actions() -> None:
    bundle = AssistantContextBundle(
        title="Incident token=titleSecret",
        facts={},
        suggested_actions=("rotate password=actionSecret", "notify Bearer actionBearer"),
    )

    prompt = bundle.to_prompt()

    assert prompt == (
        "Incident: Incident token=<redacted>\n"
        "Facts:\n"
        "Suggested actions:\n"
        "- rotate password=<redacted>\n"
        "- notify Bearer <redacted>"
    )
    assert "titleSecret" not in prompt
    assert "actionSecret" not in prompt
    assert "actionBearer" not in prompt


def test_assistant_context_to_prompt_redacts_authorization_bearer_and_quoted_secret_values() -> (
    None
):
    bundle = AssistantContextBundle(
        title="Incident",
        facts={
            "authorization_header": "Authorization Bearer deadbeef",
            "authorization_colon": "Authorization: Bearer cafebabe",
            "quoted_secret": 'password="hunter two" failed',
            "quoted_secret_colon": "api-key: 'key with spaces'",
        },
        suggested_actions=(),
    )

    prompt = bundle.to_prompt()

    assert prompt == (
        "Incident: Incident\n"
        "Facts:\n"
        "- authorization_colon: Authorization: Bearer <redacted>\n"
        "- authorization_header: Authorization Bearer <redacted>\n"
        "- quoted_secret: password=<redacted> failed\n"
        "- quoted_secret_colon: api-key=<redacted>\n"
        "Suggested actions:"
    )
    assert "deadbeef" not in prompt
    assert "cafebabe" not in prompt
    assert "hunter two" not in prompt
    assert "key with spaces" not in prompt


def test_assistant_context_to_prompt_redacts_secret_like_fact_keys() -> None:
    bundle = AssistantContextBundle(
        title="Incident",
        facts={
            "token=abc123": "failed",
            "token=def456": "retry",
            "table": "silver.orders",
        },
        suggested_actions=(),
    )

    prompt = bundle.to_prompt()

    assert prompt == (
        "Incident: Incident\n"
        "Facts:\n"
        "- table: silver.orders\n"
        "- token=<redacted>: failed\n"
        "- token=<redacted> (2): retry\n"
        "Suggested actions:"
    )
    assert "abc123" not in prompt
    assert "def456" not in prompt


def test_assistant_context_to_prompt_preserves_structured_fact_values() -> None:
    bundle = AssistantContextBundle(
        title="Incident",
        facts={
            "failed_rows": 12,
            "checks": ["not_null(order_id)", "token=abc123"],
        },
        suggested_actions=(),
    )

    prompt = bundle.to_prompt()

    assert prompt == (
        "Incident: Incident\n"
        "Facts:\n"
        "- checks: ['not_null(order_id)', 'token=<redacted>']\n"
        "- failed_rows: 12\n"
        "Suggested actions:"
    )
    assert "abc123" not in prompt


def test_assistant_context_to_prompt_redacts_values_for_nested_secret_like_keys() -> None:
    bundle = AssistantContextBundle(
        title="Incident",
        facts={
            "metadata": {
                "password": "hunter2",
                "api_key": "abc123",
            },
        },
        suggested_actions=(),
    )

    prompt = bundle.to_prompt()

    assert prompt == (
        "Incident: Incident\n"
        "Facts:\n"
        "- metadata: {'password': '<redacted>', 'api_key': '<redacted>'}\n"
        "Suggested actions:"
    )
    assert "hunter2" not in prompt
    assert "abc123" not in prompt


def test_assistant_context_serializes_mcp_payload() -> None:
    bundle = AssistantContextBundle(
        title="Quality failure",
        facts={"table": "silver.orders"},
        suggested_actions=("inspect_quality_check",),
    )

    assert bundle.to_mcp_payload() == {
        "kind": "phlo.assistant.context.v1",
        "payload": {
            "title": "Quality failure",
            "facts": {"table": "silver.orders"},
            "suggested_actions": ["inspect_quality_check"],
        },
    }


def test_assistant_context_mcp_payload_uses_redacted_read_model() -> None:
    bundle = AssistantContextBundle(
        title="Incident token=titleSecret",
        facts={"dsn": "postgresql://user:pass@localhost/db"},
        suggested_actions=("notify Bearer actionBearer",),
    )

    payload = bundle.to_mcp_payload()

    assert payload == {
        "kind": "phlo.assistant.context.v1",
        "payload": {
            "title": "Incident token=<redacted>",
            "facts": {"dsn": "<redacted-dsn>"},
            "suggested_actions": ["notify Bearer <redacted>"],
        },
    }
    assert "titleSecret" not in str(payload)
    assert "user:pass" not in str(payload)
    assert "actionBearer" not in str(payload)
