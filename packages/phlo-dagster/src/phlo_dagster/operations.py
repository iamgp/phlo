"""Dagster operational capability adapter for Phlo API mutation routes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx

from phlo.security.service_identity import build_service_headers


LAUNCH_PIPELINE_EXECUTION_MUTATION = """
mutation LaunchPipelineExecution($executionParams: ExecutionParams!) {
    launchPipelineExecution(executionParams: $executionParams) {
        __typename
        ... on LaunchRunSuccess { run { runId status } }
        ... on PipelineNotFoundError { message }
        ... on InvalidSubsetError { message }
        ... on RunConfigValidationInvalid { errors { message } }
        ... on PythonError { message }
    }
}
"""

LAUNCH_PIPELINE_REEXECUTION_MUTATION = """
mutation LaunchPipelineReexecution($executionParams: ExecutionParams, $reexecutionParams: ReexecutionParams) {
    launchPipelineReexecution(executionParams: $executionParams, reexecutionParams: $reexecutionParams) {
        __typename
        ... on LaunchRunSuccess { run { runId status } }
        ... on PythonError { message }
    }
}
"""

TERMINATE_RUN_MUTATION = """
mutation TerminateRun($runId: String!) {
    terminateRun(runId: $runId) {
        __typename
        ... on TerminateRunSuccess { run { runId status } }
        ... on RunNotFoundError { message }
        ... on PythonError { message }
    }
}
"""

LAUNCH_PARTITION_BACKFILL_MUTATION = """
mutation LaunchPartitionBackfill($backfillParams: LaunchBackfillParams!) {
    launchPartitionBackfill(backfillParams: $backfillParams) {
        __typename
        ... on LaunchBackfillSuccess { backfillId launchedRunIds }
        ... on PartitionSetNotFoundError { message }
        ... on PythonError { message }
    }
}
"""

PARTITION_KEYS_QUERY = """
query PartitionKeys($assetKey: AssetKeyInput!) {
    assetNodeOrError(assetKey: $assetKey) {
        __typename
        ... on AssetNode {
            partitionKeysByDimension { name partitionKeys }
        }
        ... on AssetNotFoundError { message }
    }
}
"""


@dataclass(frozen=True)
class DagsterOperationResult:
    """Provider-neutral result returned by the Dagster operation adapter."""

    operation: str
    dry_run: bool
    accepted: bool
    status: str
    message: str
    run_id: str | None = None
    asset_key_path: str | None = None
    partition_key: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "dry_run": self.dry_run,
            "accepted": self.accepted,
            "run_id": self.run_id,
            "asset_key_path": self.asset_key_path,
            "partition_key": self.partition_key,
            "status": self.status,
            "message": self.message,
            "details": self.details,
        }


async def launch_materialize(
    *,
    dagster_url: str,
    asset_key_path: str,
    job_name: str,
    repository_location_name: str | None = None,
    repository_name: str | None = None,
    partition_key: str | None = None,
    run_config: dict[str, Any] | None = None,
    tags: dict[str, str] | None = None,
) -> DagsterOperationResult:
    execution_tags = {"phlo/operation": "materialize_asset", "phlo/asset_key": asset_key_path}
    execution_tags.update(tags or {})
    if partition_key:
        execution_tags.setdefault("dagster/partition", partition_key)
    result = await _graphql(
        dagster_url,
        LAUNCH_PIPELINE_EXECUTION_MUTATION,
        {
            "executionParams": {
                "selector": {
                    "pipelineName": job_name,
                    "repositoryLocationName": repository_location_name,
                    "repositoryName": repository_name,
                    "assetSelection": [{"path": asset_key_path.split("/")}],
                },
                "runConfigData": run_config or {},
                "mode": "default",
                "executionMetadata": {"tags": _tags_for_execution(execution_tags)},
            }
        },
    )
    return _launch_result(
        operation="materialize_asset",
        dry_run=False,
        payload=result.get("data", {}).get("launchPipelineExecution", {}),
        asset_key_path=asset_key_path,
        partition_key=partition_key,
    )


async def launch_retry(
    *,
    dagster_url: str,
    run_id: str,
    strategy: str,
    tags: dict[str, str] | None = None,
) -> DagsterOperationResult:
    execution_tags = {"phlo/operation": "retry_failed_run", "phlo/parent_run_id": run_id}
    execution_tags.update(tags or {})
    result = await _graphql(
        dagster_url,
        LAUNCH_PIPELINE_REEXECUTION_MUTATION,
        {
            "executionParams": None,
            "reexecutionParams": {
                "parentRunId": run_id,
                "strategy": strategy,
                "extraTags": _tags_for_execution(execution_tags),
                "useParentRunTags": True,
            },
        },
    )
    return _launch_result(
        operation="retry_failed_run",
        dry_run=False,
        payload=result.get("data", {}).get("launchPipelineReexecution", {}),
        fallback_run_id=run_id,
    )


async def terminate(
    *,
    dagster_url: str,
    run_id: str,
    reason: str | None = None,
) -> DagsterOperationResult:
    result = await _graphql(dagster_url, TERMINATE_RUN_MUTATION, {"runId": run_id})
    payload = result.get("data", {}).get("terminateRun", {})
    typename = str(payload.get("__typename") or "TerminateRunResult")
    run = payload.get("run") if isinstance(payload.get("run"), dict) else {}
    accepted = typename == "TerminateRunSuccess"
    return DagsterOperationResult(
        operation="cancel_run",
        dry_run=False,
        accepted=accepted,
        run_id=str(run.get("runId") or run_id),
        status=str(run.get("status") or typename),
        message="Dagster accepted run cancellation." if accepted else _error_message(payload),
        details={"typename": typename, "reason": reason},
    )


async def launch_backfill(
    *,
    dagster_url: str,
    asset_key_path: str,
    partition_set_name: str,
    partition_keys: list[str],
    repository_location_name: str | None = None,
    repository_name: str | None = None,
    tags: dict[str, str] | None = None,
) -> DagsterOperationResult:
    execution_tags = {"phlo/operation": "backfill_asset", "phlo/asset_key": asset_key_path}
    execution_tags.update(tags or {})
    result = await _graphql(
        dagster_url,
        LAUNCH_PARTITION_BACKFILL_MUTATION,
        {
            "backfillParams": {
                "selector": {
                    "partitionSetName": partition_set_name,
                    "repositorySelector": {
                        "repositoryLocationName": repository_location_name,
                        "repositoryName": repository_name,
                    },
                },
                "partitionNames": partition_keys,
                "tags": _tags_for_execution(execution_tags),
            }
        },
    )
    payload = result.get("data", {}).get("launchPartitionBackfill", {})
    typename = str(payload.get("__typename") or "LaunchBackfillResult")
    accepted = typename == "LaunchBackfillSuccess"
    backfill_id = payload.get("backfillId")
    return DagsterOperationResult(
        operation="backfill_asset",
        dry_run=False,
        accepted=accepted,
        run_id=str(backfill_id) if backfill_id else None,
        asset_key_path=asset_key_path,
        status=typename,
        message="Dagster accepted partition backfill." if accepted else _error_message(payload),
        details={"partitions": partition_keys, "partition_count": len(partition_keys)},
    )


async def list_partitions(*, dagster_url: str, asset_key_path: str) -> list[dict[str, str]]:
    result = await _graphql(
        dagster_url,
        PARTITION_KEYS_QUERY,
        {"assetKey": {"path": asset_key_path.split("/")}},
    )
    payload = result.get("data", {}).get("assetNodeOrError", {})
    if payload.get("message"):
        raise RuntimeError(str(payload["message"]))
    keys: list[str] = []
    for dimension in payload.get("partitionKeysByDimension", []) or []:
        if isinstance(dimension, dict):
            keys.extend(str(key) for key in dimension.get("partitionKeys", []) or [])
    return [{"partition_key": key, "status": "UNKNOWN"} for key in keys]


async def _graphql(url: str, query: str, variables: dict[str, Any]) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    try:
        headers.update(build_service_headers("phlo-api", initiator="observatory"))
    except RuntimeError:
        pass
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            url, json={"query": query, "variables": variables}, headers=headers
        )
        response.raise_for_status()
        payload = response.json()
    if payload.get("errors"):
        raise RuntimeError(payload["errors"][0].get("message", "GraphQL error"))
    return payload


def _launch_result(
    *,
    operation: str,
    dry_run: bool,
    payload: dict[str, Any],
    asset_key_path: str | None = None,
    partition_key: str | None = None,
    fallback_run_id: str | None = None,
) -> DagsterOperationResult:
    typename = str(payload.get("__typename") or "DagsterLaunchResult")
    run = payload.get("run") if isinstance(payload.get("run"), dict) else {}
    accepted = typename in {"LaunchRunSuccess", "LaunchPipelineRunSuccess"} and bool(run)
    return DagsterOperationResult(
        operation=operation,
        dry_run=dry_run,
        accepted=accepted,
        run_id=str(run.get("runId") or fallback_run_id) if (run or fallback_run_id) else None,
        asset_key_path=asset_key_path,
        partition_key=partition_key,
        status=str(run.get("status") or typename),
        message=f"Dagster accepted {operation}." if accepted else _error_message(payload),
        details={"typename": typename},
    )


def _error_message(payload: dict[str, Any]) -> str:
    if payload.get("message"):
        return str(payload["message"])
    errors = payload.get("errors")
    if isinstance(errors, list) and errors:
        first = errors[0]
        if isinstance(first, dict) and first.get("message"):
            return str(first["message"])
    return str(payload.get("__typename") or "Dagster operation failed")


def _tags_for_execution(tags: dict[str, str]) -> list[dict[str, str]]:
    return [{"key": str(key), "value": str(value)} for key, value in tags.items()]
