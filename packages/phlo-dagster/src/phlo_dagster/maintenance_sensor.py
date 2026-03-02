"""
Dagster sensor and ops for policy-driven Iceberg table maintenance.

Evaluates table statistics against configured policies and triggers
maintenance jobs when thresholds are exceeded.
"""

import os
from typing import Any

import dagster as dg

from phlo.logging import get_logger

from phlo_dagster.iceberg_maintenance_utils import list_tables
from phlo_dagster.maintenance_policy import (
    NamespacePolicy,
    TableAction,
    evaluate_table,
    load_policies,
)

logger = get_logger(__name__)

_DEFAULT_POLICY_PATH = "maintenance_policy.yaml"


def _load_iceberg_stats() -> Any:
    """Load get_table_stats lazily for optional integration support."""
    try:
        from phlo_iceberg.tables import get_table_stats
    except Exception as exc:  # noqa: BLE001 - runtime guidance for optional dependency
        raise RuntimeError(
            "Iceberg maintenance requires phlo-iceberg. Install phlo-dagster[iceberg] "
            "or phlo-iceberg."
        ) from exc
    return get_table_stats


def _load_trino() -> Any:
    """Load TrinoResource lazily for optional integration support."""
    try:
        from phlo_trino.resource import TrinoResource
    except Exception as exc:  # noqa: BLE001 - runtime guidance for optional dependency
        raise RuntimeError(
            "Trino OPTIMIZE requires phlo-trino. Install phlo-dagster[trino] or phlo-trino."
        ) from exc
    return TrinoResource


def _evaluate_namespace(
    policy: NamespacePolicy,
    get_table_stats: Any,
    context: dg.SensorEvaluationContext,
) -> list[TableAction]:
    """Evaluate all tables in a namespace against a policy.

    Returns list of TableActions that have at least one action flagged.
    """
    actions: list[TableAction] = []
    tables = list_tables(policy.namespace, policy.ref)

    for table_name in tables:
        try:
            stats = get_table_stats(table_name=table_name, ref=policy.ref)
        except Exception:
            logger.exception("maintenance_sensor_stats_failed", table_name=table_name)
            continue

        action = evaluate_table(table_name, stats, policy)
        if action.expire_snapshots or action.optimize:
            actions.append(action)

    return actions


class OptimizeConfig(dg.Config):
    """Configuration for the Trino OPTIMIZE op."""

    table_names: list[str]
    ref: str = "main"


@dg.op
def optimize_table_files(
    context: dg.OpExecutionContext,
    config: OptimizeConfig,
) -> dict[str, Any]:
    """Run Trino OPTIMIZE on tables to compact small files."""
    TrinoResource = _load_trino()
    trino = TrinoResource()
    results: list[dict[str, Any]] = []
    errors: list[str] = []

    for table_name in config.table_names:
        try:
            trino.execute(f"ALTER TABLE {table_name} EXECUTE optimize")
            context.log.info(f"Optimized table {table_name}")
            results.append({"table_name": table_name, "status": "success"})
        except Exception as e:
            error_msg = f"Failed to optimize {table_name}: {e}"
            context.log.warning(error_msg)
            errors.append(error_msg)
            results.append({"table_name": table_name, "status": "error", "error": str(e)})

    return {"results": results, "errors": errors}


@dg.job(description="Optimize Iceberg table files via Trino EXECUTE optimize")
def optimize_tables_job():
    """Job that runs Trino OPTIMIZE on selected tables."""
    optimize_table_files()


@dg.sensor(
    name="maintenance_policy_sensor",
    description=(
        "Evaluates table stats against maintenance policies "
        "and triggers maintenance when thresholds are exceeded"
    ),
    minimum_interval_seconds=1800,
    default_status=dg.DefaultSensorStatus.STOPPED,
    jobs=[optimize_tables_job],
)
def maintenance_policy_sensor(context: dg.SensorEvaluationContext):
    """Evaluate tables against maintenance policies, yield RunRequests as needed."""
    policy_path = os.environ.get("PHLO_MAINTENANCE_POLICY_PATH", _DEFAULT_POLICY_PATH)

    try:
        policies = load_policies(policy_path)
    except Exception:
        logger.exception("maintenance_sensor_policy_load_failed", path=policy_path)
        return

    get_table_stats = _load_iceberg_stats()

    for policy in policies:
        actions = _evaluate_namespace(policy, get_table_stats, context)
        if not actions:
            continue

        expire_tables = [a.table_name for a in actions if a.expire_snapshots]
        optimize_tables = [a.table_name for a in actions if a.optimize]

        if expire_tables:
            logger.info(
                "maintenance_sensor_expire_triggered",
                namespace=policy.namespace,
                table_count=len(expire_tables),
            )
            yield dg.RunRequest(
                run_key=f"expire_{policy.namespace}_{context.cursor or 'init'}",
                job_name="expire_snapshots_job",
                run_config=dg.RunConfig(
                    ops={
                        "expire_table_snapshots": {
                            "config": {
                                "namespace": policy.namespace,
                                "ref": policy.ref,
                                "snapshot_retention_days": (
                                    policy.expire.older_than_days if policy.expire else 7
                                ),
                                "snapshot_retain_last": (
                                    policy.expire.retain_last if policy.expire else 5
                                ),
                                "table_allowlist": expire_tables,
                            }
                        }
                    }
                ),
            )

        if optimize_tables:
            logger.info(
                "maintenance_sensor_optimize_triggered",
                namespace=policy.namespace,
                table_count=len(optimize_tables),
            )
            yield dg.RunRequest(
                run_key=f"optimize_{policy.namespace}_{context.cursor or 'init'}",
                job_name="optimize_tables_job",
                run_config=dg.RunConfig(
                    ops={
                        "optimize_table_files": {
                            "config": {
                                "table_names": optimize_tables,
                                "ref": policy.ref,
                            }
                        }
                    }
                ),
            )


def get_policy_maintenance_definitions() -> dg.Definitions:
    """Get Dagster definitions for policy-driven maintenance.

    Returns definitions including the policy sensor and optimize job,
    to be merged into a project's main definitions.

    Example::

        from phlo_dagster.maintenance_sensor import get_policy_maintenance_definitions

        policy_defs = get_policy_maintenance_definitions()
        defs = dg.Definitions.merge(your_defs, policy_defs)
    """
    logger.info(
        "dagster_policy_maintenance_definitions_built",
        job_count=1,
        sensor_count=1,
    )
    return dg.Definitions(
        jobs=[optimize_tables_job],
        sensors=[maintenance_policy_sensor],
    )
