"""Data product portal read models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from phlo.governance.catalog import GovernanceCatalog, GovernedDataset


@dataclass(frozen=True, slots=True)
class DataProduct:
    id: str
    title: str
    owner: str
    description: str | None
    domain: str | None
    classification: str | None
    certification: str
    status: str
    tags: dict[str, str] = field(default_factory=dict)
    access_request: dict[str, Any] = field(default_factory=dict)

    def to_read_model(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "owner": self.owner,
            "description": self.description,
            "domain": self.domain,
            "classification": self.classification,
            "certification": self.certification,
            "status": self.status,
            "tags": _copy_json_like(self.tags),
            "access_request": _copy_json_like(self.access_request),
        }


def _copy_json_like(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _copy_json_like(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_copy_json_like(item) for item in value]
    return value


def _product_from_dataset(dataset: GovernedDataset, status: str) -> DataProduct:
    certification = dataset.tags.get("certification", "uncertified")
    return DataProduct(
        id=dataset.id,
        title=dataset.id,
        owner=dataset.owner,
        description=dataset.description,
        domain=dataset.tags.get("domain"),
        classification=dataset.classification,
        certification=certification,
        status=status,
        tags=dict(dataset.tags),
        access_request={"dataset_id": dataset.id, "policy_ids": list(dataset.policies)},
    )


def build_data_products(
    *,
    catalog: GovernanceCatalog,
    statuses: dict[str, str] | None = None,
) -> list[DataProduct]:
    """Build browser-safe data product cards from governance metadata."""
    status_by_id = statuses or {}
    return [
        _product_from_dataset(dataset, status_by_id.get(dataset.id, "unknown"))
        for dataset in catalog.datasets.values()
    ]


def build_access_request(*, dataset_id: str, requester: str, reason: str) -> dict[str, str]:
    """Build a browser-safe access request payload for workflow handoff."""
    return {
        "dataset_id": dataset_id,
        "requester": requester,
        "reason": reason,
        "status": "pending",
    }
