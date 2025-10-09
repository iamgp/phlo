from __future__ import annotations

import os
from datetime import datetime, timezone
from uuid import uuid4

from dagster import AssetKey, asset
from openlineage.client.event_v2 import InputDataset, OutputDataset, Job, Run, RunEvent, RunState


@asset(
    group_name="lineage",
    description="Emits OpenLineage dataset events for the Nightscout Airbyte ingestion.",
    non_argument_deps={AssetKey(["nightscout_entries"])},
    required_resource_keys={"openlineage"},
)
def nightscout_airbyte_lineage(context) -> str:
    """
    Emit OpenLineage events linking the Nightscout API to the raw Nightscout dataset
    produced by the Airbyte sync. This makes the ingestion step visible in Marquez.
    """

    client = context.resources.openlineage.get_client()
    namespace = os.getenv("OPENLINEAGE_NAMESPACE", "lakehouse")
    run_id = str(uuid4())
    job_name = "airbyte.nightscout_to_raw"
    now = datetime.now(timezone.utc).isoformat()

    input_dataset = InputDataset(
        namespace="nightscout.api",
        name="entries",
        facets={},
    )

    output_dataset = OutputDataset(
        namespace=f"{namespace}.raw",
        name="nightscout_entries",
        facets={},
    )

    job = Job(namespace=namespace, name=job_name)
    run = Run(runId=run_id)

    client.emit(
        RunEvent(
            eventType=RunState.START,
            eventTime=now,
            run=run,
            job=job,
        )
    )

    client.emit(
        RunEvent(
            eventType=RunState.COMPLETE,
            eventTime=datetime.now(timezone.utc).isoformat(),
            run=run,
            job=job,
            inputs=[input_dataset],
            outputs=[output_dataset],
        )
    )

    context.add_output_metadata({"run_id": run_id})
    return run_id
