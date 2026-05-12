from phlo.capabilities import WorkflowContributionMode
from phlo_sling.plugin import get_workflow_wizard_contributions


def test_sling_contributes_replication_source_wizard() -> None:
    contributions = get_workflow_wizard_contributions()

    contribution = contributions[0]
    payload = contribution.to_browser_dict()

    assert payload["id"] == "sling.replication-source"
    assert payload["stage"] == "source"
    assert payload["package"] == "phlo-sling"
    assert WorkflowContributionMode.APPLY in contribution.modes
    assert [field["name"] for field in payload["fields"]] == [
        "domain",
        "source_name",
        "source_stream",
        "target_table",
        "primary_key",
        "replication_mode",
        "update_key",
        "schedule",
    ]
