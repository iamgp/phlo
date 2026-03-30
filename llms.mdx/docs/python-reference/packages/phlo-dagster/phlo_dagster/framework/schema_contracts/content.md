# schema_contracts (/docs/python-reference/packages/phlo-dagster/phlo_dagster/framework/schema_contracts)



Schema contract refresh integration for Dagster materialization flows.

This module provides automatic schema contract refresh functionality
that integrates with Dagster asset materialization. When enabled via
environment variables, it refreshes Pandera schema contracts before
materializing assets to ensure data contracts stay synchronized with
the actual data.

Environment Variables:
PHLO\_AUTO\_REFRESH\_CONTRACTS: Enable automatic refresh (1/true/yes)
PHLO\_CONTRACT\_REFRESH\_SELECTION: Asset selection for contract refresh

Integration Point:
Called during framework definitions building, before user workflows
are discovered. This ensures contracts are fresh before any
materialization occurs.

Schema Contract Purpose:
Pandera schema contracts define expected data schemas and
validation rules. Keeping them synchronized with actual table
schemas helps catch schema drift and maintain data quality.

Example:
Enabling auto-refresh::

export PHLO\_AUTO\_REFRESH\_CONTRACTS=1
export PHLO\_CONTRACT\_REFRESH\_SELECTION="tag:bronze"

phlo materialize my\_asset

Contracts will be refreshed before materialization [#contracts-will-be-refreshed-before-materialization]

<Tabs items="[&#x22;Functions&#x22;]">
  <Tab value="&#x22;Functions&#x22;">
    <PyFunction name="&#x22;maybe_refresh_contracts&#x22;" type="&#x22;(workflows_path, logger) -> None&#x22;">
      Refresh schema contracts when explicitly enabled via env vars.

      <PySourceCode>
        ```python
        def maybe_refresh_contracts(workflows_path: Path, logger: Any) -> None:
            """Refresh schema contracts when explicitly enabled via env vars.

            Args:
                workflows_path: Path to workflows directory used for contract resolution.
                logger: Logger instance for operation logging.

            Returns:
                None

            Raises:
                No explicit exceptions raised. Logs warnings on failure.

            """
            enabled = os.getenv("PHLO_AUTO_REFRESH_CONTRACTS", "").strip().lower()
            if enabled not in {"1", "true", "yes"}:
                return

            selection = os.getenv("PHLO_CONTRACT_REFRESH_SELECTION")

            try:
                from phlo.cli.commands.schema_migrate import refresh_contracts_for_selection
            except Exception:
                logger.warning(
                    "schema_contract_refresh_unavailable",
                    workflows_path=str(workflows_path),
                    selection=selection,
                    exc_info=True,
                )
                return

            try:
                refreshed_count = refresh_contracts_for_selection(selection=selection, force=True)
            except Exception:
                logger.warning(
                    "schema_contract_refresh_failed",
                    workflows_path=str(workflows_path),
                    selection=selection,
                    exc_info=True,
                )
                return

            logger.info(
                "schema_contract_refresh_completed",
                workflows_path=str(workflows_path),
                selection=selection,
                refreshed_count=refreshed_count,
            )
        ```
      </PySourceCode>

      <div>
        <PyParameter name="&#x22;workflows_path&#x22;" type="&#x22;Path&#x22;" value="undefined">
          Path to workflows directory used for contract resolution.
        </PyParameter>

        <PyParameter name="&#x22;logger&#x22;" type="&#x22;Any&#x22;" value="undefined">
          Logger instance for operation logging.
        </PyParameter>
      </div>

      <PyFunctionReturn type="&#x22;None&#x22;">
        None
      </PyFunctionReturn>
    </PyFunction>
  </Tab>
</Tabs>
