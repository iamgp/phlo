# partitions (/docs/python-reference/packages/phlo-dagster/phlo_dagster/partitions)



Shared partition definitions for phlo-dagster assets.

This module provides standard partition definitions used across Phlo's
Dagster-based orchestration layer. Partitions enable time-based slicing
of data assets for incremental processing and backfills.

Partition Types:

* daily\_partition: Daily date-based partitioning starting from 2025-01-01
  using Europe/London timezone for business-day alignment.

Usage:
Partitions are typically referenced in asset specs and applied to
ingestion and transformation assets that process data incrementally.

Example:
Using the daily partition in an asset spec::

from phlo\_dagster.partitions import daily\_partition
from phlo.capabilities import AssetSpec

spec = AssetSpec(
key="raw\.orders",
partitions=daily\_partition,

... other configuration [#-other-configuration]

)

<PyAttribute name="&#x22;daily_partition&#x22;" type="null" value="&#x22;DailyPartitionsDefinition(start_date='2025-01-01', timezone='Europe/London')&#x22;" />
