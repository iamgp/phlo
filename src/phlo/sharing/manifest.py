"""Data sharing manifest models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from phlo.governance.catalog import GovernanceCatalog


@dataclass(frozen=True, slots=True)
class ShareDataset:
    id: str
    mode: str = "read"

    def __post_init__(self) -> None:
        if self.mode != "read":
            raise ValueError(f"Shares are read-only in v1: {self.id} requested {self.mode}")

    def to_read_model(self) -> dict[str, Any]:
        return {"id": self.id, "mode": self.mode}


@dataclass(frozen=True, slots=True)
class ShareRecipient:
    id: str
    type: str

    def to_read_model(self) -> dict[str, Any]:
        return {"id": self.id, "type": self.type}


@dataclass(frozen=True, slots=True)
class ShareManifest:
    version: int
    share_id: str
    title: str | None
    datasets: tuple[ShareDataset, ...]
    recipients: tuple[ShareRecipient, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any], *, catalog: GovernanceCatalog) -> ShareManifest:
        datasets: list[ShareDataset] = []
        for raw in data.get("datasets", []):
            dataset_id = str(raw["id"])
            mode = str(raw.get("mode", "read"))
            if mode != "read":
                raise ValueError(f"Shares are read-only in v1: {dataset_id} requested {mode}")
            if dataset_id not in catalog.datasets:
                raise ValueError(f"Share references unknown governed dataset: {dataset_id}")
            datasets.append(ShareDataset(id=dataset_id, mode=mode))

        recipients = tuple(
            ShareRecipient(id=str(raw["id"]), type=str(raw["type"]))
            for raw in data.get("recipients", [])
        )

        return cls(
            version=int(data.get("version", 1)),
            share_id=str(data["share_id"]),
            title=data.get("title"),
            datasets=tuple(datasets),
            recipients=recipients,
        )

    def to_read_model(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "share_id": self.share_id,
            "title": self.title,
            "datasets": [dataset.to_read_model() for dataset in self.datasets],
            "recipients": [recipient.to_read_model() for recipient in self.recipients],
        }
