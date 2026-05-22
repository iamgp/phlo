"""Provider-neutral federation registry models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ExternalConnection:
    id: str
    type: str
    jdbc_url: str
    secret_ref: str

    def to_read_model(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
        }


@dataclass(frozen=True, slots=True)
class ForeignDataset:
    id: str
    connection_id: str
    remote_name: str
    mode: str = "query"

    def to_read_model(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "connection_id": self.connection_id,
            "remote_name": self.remote_name,
            "mode": self.mode,
        }


@dataclass(frozen=True, slots=True)
class FederationRegistry:
    version: int
    connections: dict[str, ExternalConnection]
    datasets: dict[str, ForeignDataset]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FederationRegistry:
        connections: dict[str, ExternalConnection] = {}
        for raw in data.get("connections", []):
            connection_id = str(raw["id"])
            if connection_id in connections:
                raise ValueError(f"Duplicate federation connection id: {connection_id}")
            connections[connection_id] = ExternalConnection(
                id=connection_id,
                type=str(raw["type"]),
                jdbc_url=str(raw["jdbc_url"]),
                secret_ref=str(raw["secret_ref"]),
            )

        datasets: dict[str, ForeignDataset] = {}
        for raw in data.get("datasets", []):
            dataset_id = str(raw["id"])
            if dataset_id in datasets:
                raise ValueError(f"Duplicate foreign dataset id: {dataset_id}")
            connection_id = str(raw["connection_id"])
            if connection_id not in connections:
                raise ValueError(
                    f"Foreign dataset {dataset_id} references unknown connection {connection_id}"
                )
            datasets[dataset_id] = ForeignDataset(
                id=dataset_id,
                connection_id=connection_id,
                remote_name=str(raw["remote_name"]),
                mode=str(raw.get("mode", "query")),
            )

        return cls(
            version=int(data.get("version", 1)),
            connections=connections,
            datasets=datasets,
        )

    def to_read_model(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "connections": [connection.to_read_model() for connection in self.connections.values()],
            "datasets": [dataset.to_read_model() for dataset in self.datasets.values()],
        }
