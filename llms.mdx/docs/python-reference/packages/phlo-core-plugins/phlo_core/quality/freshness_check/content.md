# freshness_check (/docs/python-reference/packages/phlo-core-plugins/phlo_core/quality/freshness_check)



Freshness check plugin for validating data timeliness.

This module provides the FreshnessCheckPlugin, which enables validation of
data freshness based on timestamp columns. It helps ensure that data is
being updated within acceptable timeframes, critical for time-sensitive
analytics and operational dashboards.

Example:
Using the freshness check plugin::

from datetime import datetime, timedelta
from phlo\_core.quality.freshness\_check import FreshnessCheckPlugin

Create the plugin [#create-the-plugin]

plugin = FreshnessCheckPlugin()

Check that data is no more than 24 hours old [#check-that-data-is-no-more-than-24-hours-old]

check = plugin.create\_check(
timestamp\_column="updated\_at",
max\_age\_hours=24.0
)

Check against a specific reference time [#check-against-a-specific-reference-time]

reference = datetime.now() - timedelta(hours=12)
check\_with\_ref = plugin.create\_check(
timestamp\_column="created\_at",
max\_age\_hours=6.0,
reference\_time=reference
)

<Tabs items="[&#x22;Class&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;FreshnessCheckPlugin&#x22;" href="&#x22;/docs/python-reference/packages/phlo-core-plugins/phlo_core/quality/freshness_check/FreshnessCheckPlugin&#x22;" />
    </Cards>
  </Tab>
</Tabs>
