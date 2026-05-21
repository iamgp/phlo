import phlo.flow as flow


def test_access_policy_records_governance_metadata() -> None:
    flow.clear_flow_declarations()

    @flow.access_policy(
        table="warehouse.customers",
        roles=["analyst"],
        pii_columns=["email"],
        policy="mask-pii",
        tags={"privacy": "restricted"},
        classification="restricted",
        row_filter="region = current_setting('phlo.region')",
        column_masks={"email": "email"},
    )
    def customers_policy() -> None:
        return None

    policy = flow.get_access_policies()[0]

    assert policy.tags == {"privacy": "restricted"}
    assert policy.classification == "restricted"
    assert policy.row_filter == "region = current_setting('phlo.region')"
    assert policy.column_masks == {"email": "email"}
