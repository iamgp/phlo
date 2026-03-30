# uniqueness_check (/docs/python-reference/packages/phlo-core-plugins/phlo_core/quality/uniqueness_check)



Uniqueness check plugin for validating primary key integrity.

This module provides the UniquenessCheckPlugin, which enables validation of
uniqueness constraints on specified columns. It helps ensure data integrity
by detecting duplicate values in columns that should contain unique identifiers,
such as primary keys or natural keys.

Example:
Using the uniqueness check plugin::

from phlo\_core.quality.uniqueness\_check import UniquenessCheckPlugin

Create the plugin [#create-the-plugin]

plugin = UniquenessCheckPlugin()

Strict uniqueness check (no duplicates allowed) [#strict-uniqueness-check-no-duplicates-allowed]

strict\_check = plugin.create\_check(
columns=\["user\_id"],
allow\_threshold=0.0
)

Lenient uniqueness check (allow up to 5% duplicates) [#lenient-uniqueness-check-allow-up-to-5-duplicates]

lenient\_check = plugin.create\_check(
columns=\["session\_id"],
allow\_threshold=0.05
)

Multi-column uniqueness check [#multi-column-uniqueness-check]

composite\_check = plugin.create\_check(
columns=\["first\_name", "last\_name", "date\_of\_birth"],
allow\_threshold=0.0
)

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;UniquenessCheckPlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-core-plugins/phlo_core/quality/uniqueness_check/UniquenessCheckPlugin&#x22;" />
    </Cards>
  </Tab>
</Tabs>
