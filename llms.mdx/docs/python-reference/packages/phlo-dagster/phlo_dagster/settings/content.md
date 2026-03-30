# settings (/docs/python-reference/packages/phlo-dagster/phlo_dagster/settings)



Configuration settings for Dagster orchestration.

This module defines the DagsterSettings class for configuring the
Dagster adapter behavior. Settings control executor selection,
workflow discovery paths, and service port configuration.

Configuration Sources:

* Environment variables (PHLO\_\* prefix)
* .phlo/.env and .phlo/.env.local files
* Default values defined in DagsterSettings

Key Settings:

* dagster\_port: Webserver port (default: 10006)
* workflows\_path: User workflow discovery path (default: workflows)
* phlo\_force\_in\_process\_executor: Force single-process execution
* phlo\_force\_multiprocess\_executor: Force multiprocess execution
* phlo\_host\_platform: Override platform detection

Executor Selection:
The module implements platform-aware executor selection to handle
Docker Desktop/Colima on macOS where multiprocessing can cause
DuckDB crashes. Priority:

1. PHLO\_FORCE\_IN\_PROCESS\_EXECUTOR
2. PHLO\_FORCE\_MULTIPROCESS\_EXECUTOR
3. PHLO\_HOST\_PLATFORM detection
4. platform.system() fallback

Example:
Accessing settings::

from phlo\_dagster.settings import get\_settings

settings = get\_settings()
port = settings.dagster\_port

Environment configuration::

PHLO\_DAGSTER\_PORT=3000
PHLO\_WORKFLOWS\_PATH=./custom\_workflows

<Tabs items="[&#x22;Class&#x22;,&#x22;Functions&#x22;]">
  <Tab value="&#x22;Class&#x22;">
    <Cards>
      <Card title="&#x22;DagsterSettings&#x22;" href="&#x22;/docs/python-reference/packages/phlo-dagster/phlo_dagster/settings/DagsterSettings&#x22;" />
    </Cards>
  </Tab>

  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;get_settings&#x22;" type="&#x22;() -> DagsterSettings&#x22;">
      Return cached Dagster settings.

      <PySourceCode>
        ```python
        @lru_cache(maxsize=1)
        def get_settings() -> DagsterSettings:
            """Return cached Dagster settings."""
            return DagsterSettings()
        ```
      </PySourceCode>

      <PyFunctionReturn type="&#x22;phlo_dagster.settings.DagsterSettings&#x22;" />
    </PyFunction>
  </Tab>
</Tabs>
