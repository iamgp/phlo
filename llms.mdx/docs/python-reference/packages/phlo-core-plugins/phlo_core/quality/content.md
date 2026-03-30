# quality (/docs/python-reference/packages/phlo-core-plugins/phlo_core/quality)



Quality check plugins bundled with Phlo.

This module provides a collection of quality check plugins that can be used
to validate data integrity, completeness, freshness, and schema conformance.
These plugins integrate with the Phlo quality framework and can be applied to
Pandera schemas or used directly in data pipelines.

Available Plugins:

* NullCheckPlugin: Checks for null values in specified columns with
  configurable thresholds.
* UniquenessCheckPlugin: Validates that specified columns contain unique
  values, with optional tolerance for duplicates.
* FreshnessCheckPlugin: Validates that timestamped data is within an
  acceptable age range.
* SchemaCheckPlugin: Validates that data conforms to an expected schema
  with correct columns and types.

Each plugin follows the QualityCheckPlugin interface and provides a
`create_check()` method to instantiate the actual check object.

Example:
Import and use quality plugins::

from phlo\_core.quality import NullCheckPlugin, FreshnessCheckPlugin

Create a null check for required columns [#create-a-null-check-for-required-columns]

null\_plugin = NullCheckPlugin()
null\_check = null\_plugin.create\_check(
columns=\["id", "name", "email"],
allow\_threshold=0.01  # Allow up to 1% nulls
)

Create a freshness check for data age [#create-a-freshness-check-for-data-age]

freshness\_plugin = FreshnessCheckPlugin()
freshness\_check = freshness\_plugin.create\_check(
timestamp\_column="created\_at",
max\_age\_hours=24
)

<PyAttribute name="&#x22;__all__&#x22;" type="null" value="&#x22;['NullCheckPlugin', 'UniquenessCheckPlugin', 'FreshnessCheckPlugin', 'SchemaCheckPlugin']&#x22;" />

<Tabs items="[&#x22;Modules&#x22;]">
  <Tab value="&#x22;Modules&#x22;">
    <Cards>
      <Card href="&#x22;/docs/python-reference/packages/phlo-core-plugins/phlo_core/quality/schema_check&#x22;" title="&#x22;schema_check&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-core-plugins/phlo_core/quality/freshness_check&#x22;" title="&#x22;freshness_check&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-core-plugins/phlo_core/quality/uniqueness_check&#x22;" title="&#x22;uniqueness_check&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-core-plugins/phlo_core/quality/null_check&#x22;" title="&#x22;null_check&#x22;" />
    </Cards>
  </Tab>
</Tabs>
