from phlo.capabilities import WorkflowContributionMode
from phlo_dbt.plugin import get_workflow_wizard_contributions


def test_dbt_contributes_transform_wizard_options() -> None:
    contributions = get_workflow_wizard_contributions()

    ids = [contribution.id for contribution in contributions]

    assert ids == [
        "dbt.initialize-project",
        "dbt.basic-model",
        "dbt.source-yml",
        "dbt.schema-tests",
    ]
    assert all(contribution.stage == "transform" for contribution in contributions)
    assert all(
        WorkflowContributionMode.PROPOSAL in contribution.modes for contribution in contributions
    )
    assert "model_name" in [field.name for field in contributions[1].fields]
    assert "source_name" in [field.name for field in contributions[2].fields]
    assert "unique_key" in [field.name for field in contributions[3].fields]
