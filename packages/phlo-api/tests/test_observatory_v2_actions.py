from phlo_api.observatory_api.v2_actions import execute_v2_action
from phlo_api.observatory_api.v2_models import V2Action, V2ActionRequest


def test_v2_action_exposes_guard_metadata() -> None:
    action = V2Action(
        id="service:trino:restart",
        label="Restart",
        kind="service.restart",
        enabled=True,
        risk_level="medium",
        required_capability="service_control",
        required_service="trino",
        required_permission="service.manage",
        equivalent_cli_command="phlo services restart --service trino",
        expected_evidence=["service.status.running"],
    )
    payload = action.model_dump()
    assert payload["risk_level"] == "medium"
    assert payload["required_permission"] == "service.manage"
    assert payload["expected_evidence"] == ["service.status.running"]


def test_execute_v2_action_rejects_unknown_action() -> None:
    result = execute_v2_action(V2ActionRequest(action_id="unknown:thing"))
    assert result.status == "failed"
    assert "Unsupported" in result.message


def test_execute_v2_action_returns_skipped_for_unimplemented_known_family() -> None:
    result = execute_v2_action(V2ActionRequest(action_id="quality:orders:not_null:rerun"))
    assert result.status == "skipped"
    assert result.action.kind == "quality.rerun"
    assert result.action.required_capability == "quality_backend"
