"""Provider-neutral governance catalog models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class GovernedColumn:
    name: str
    classification: str | None = None
    mask: str | None = None
    tags: dict[str, str] = field(default_factory=dict)

    def to_read_model(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "classification": self.classification,
            "mask": self.mask,
            "tags": dict(self.tags),
        }


@dataclass(frozen=True, slots=True)
class RowFilter:
    name: str
    expression: str
    applies_to_roles: tuple[str, ...] = ()

    def to_read_model(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "expression": self.expression,
            "applies_to_roles": list(self.applies_to_roles),
        }


@dataclass(frozen=True, slots=True)
class GovernedDataset:
    id: str
    owner: str
    description: str | None = None
    classification: str | None = None
    tags: dict[str, str] = field(default_factory=dict)
    columns: dict[str, GovernedColumn] = field(default_factory=dict)
    row_filters: tuple[RowFilter, ...] = ()
    policies: tuple[str, ...] = ()

    def to_read_model(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "owner": self.owner,
            "description": self.description,
            "classification": self.classification,
            "tags": dict(self.tags),
            "columns": [column.to_read_model() for column in self.columns.values()],
            "row_filters": [row_filter.to_read_model() for row_filter in self.row_filters],
            "policies": list(self.policies),
        }


@dataclass(frozen=True, slots=True)
class GovernanceCatalog:
    version: int
    datasets: dict[str, GovernedDataset]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GovernanceCatalog:
        datasets: dict[str, GovernedDataset] = {}
        for raw in data.get("datasets", []):
            dataset_id = str(raw["id"])
            if dataset_id in datasets:
                raise ValueError(f"Duplicate dataset id: {dataset_id}")
            raw_columns = raw.get("columns", {})
            columns = {
                name: GovernedColumn(
                    name=name,
                    classification=column.get("classification"),
                    mask=column.get("mask"),
                    tags=dict(column.get("tags", {})),
                )
                for name, column in raw_columns.items()
            }
            row_filters = tuple(
                RowFilter(
                    name=str(row_filter["name"]),
                    expression=str(row_filter["expression"]),
                    applies_to_roles=tuple(row_filter.get("applies_to_roles", ())),
                )
                for row_filter in raw.get("row_filters", [])
            )
            datasets[dataset_id] = GovernedDataset(
                id=dataset_id,
                owner=str(raw["owner"]),
                description=raw.get("description"),
                classification=raw.get("classification"),
                tags=dict(raw.get("tags", {})),
                columns=columns,
                row_filters=row_filters,
                policies=tuple(raw.get("policies", ())),
            )
        return cls(version=int(data.get("version", 1)), datasets=datasets)

    def dataset(self, dataset_id: str) -> GovernedDataset:
        return self.datasets[dataset_id]

    def to_read_model(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "datasets": [dataset.to_read_model() for dataset in self.datasets.values()],
        }
