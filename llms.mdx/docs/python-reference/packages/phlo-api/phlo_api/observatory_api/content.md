# observatory_api (/docs/python-reference/packages/phlo-api/phlo_api/observatory_api)



Observatory API.

FastAPI routers for Observatory backend functionality.
These replace the TanStack Start server functions and enable
Observatory to run as a pure SPA with a Python backend.

This package provides endpoints for:

* Data exploration (Trino, Iceberg tables)
* Orchestration (Dagster integration)
* Data versioning (Nessie)
* Quality monitoring
* Log analysis (Loki)
* Lineage tracking
* Search and discovery
* Settings management

Example:
Routers are auto-discovered and registered by main.py:

.. code-block:: python

from phlo\_api.observatory\_api.trino import router
app.include\_router(router, prefix="/api/trino")

<Tabs items="[&#x22;Modules&#x22;]">
  <Tab value="&#x22;Modules&#x22;">
    <Cards>
      <Card href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/trino&#x22;" title="&#x22;trino&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/contributing&#x22;" title="&#x22;contributing&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/loki&#x22;" title="&#x22;loki&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/search&#x22;" title="&#x22;search&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/dagster&#x22;" title="&#x22;dagster&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/settings&#x22;" title="&#x22;settings&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/quality&#x22;" title="&#x22;quality&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/trino_sql&#x22;" title="&#x22;trino_sql&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/extensions&#x22;" title="&#x22;extensions&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/lineage&#x22;" title="&#x22;lineage&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/extension_settings&#x22;" title="&#x22;extension_settings&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/nessie&#x22;" title="&#x22;nessie&#x22;" />

      <Card href="&#x22;/docs/python-reference/packages/phlo-api/phlo_api/observatory_api/iceberg&#x22;" title="&#x22;iceberg&#x22;" />
    </Cards>
  </Tab>
</Tabs>
