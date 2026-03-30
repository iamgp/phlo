# null_check (/docs/python-reference/packages/phlo-core-plugins/phlo_core/quality/null_check)



Null check plugin for validating column completeness.

This module provides the NullCheckPlugin, which enables validation of
null value presence in specified columns. It helps ensure data completeness
by detecting missing values and enforcing thresholds for acceptable null rates.

Example:
Using the null check plugin::

from phlo\_core.quality.null\_check import NullCheckPlugin

Create the plugin [#create-the-plugin]

plugin = NullCheckPlugin()

Strict null check (no nulls allowed) [#strict-null-check-no-nulls-allowed]

strict\_check = plugin.create\_check(
columns=\["id", "email", "created\_at"],
allow\_threshold=0.0
)

Lenient null check (allow up to 10% nulls in optional fields) [#lenient-null-check-allow-up-to-10-nulls-in-optional-fields]

lenient\_check = plugin.create\_check(
columns=\["middle\_name", "phone\_number"],
allow\_threshold=0.10
)

Mixed columns with different requirements [#mixed-columns-with-different-requirements]

mixed\_check = plugin.create\_check(
columns=\["required\_field", "optional\_field"],
allow\_threshold=0.0  # Applies to all columns
)

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;NullCheckPlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-core-plugins/phlo_core/quality/null_check/NullCheckPlugin&#x22;" />
    </Cards>
  </Tab>
</Tabs>
