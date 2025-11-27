"""
Data contract definition and validation.

Defines contract format, loading, validation, and registry management.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

import yaml


class ChangeType(str, Enum):
    """Type of schema change for contract enforcement."""

    SAFE = "safe"
    WARNING = "warning"
    BREAKING = "breaking"


@dataclass
class SLAConfig:
    """Service-level agreement configuration for data contracts."""

    freshness_hours: Optional[int] = None
    """Maximum age of data in hours (freshness SLA)."""

    quality_threshold: float = 0.99
    """Minimum fraction of rows that must pass quality checks (0-1)."""

    availability_percentage: float = 99.9
    """Minimum availability percentage for the table."""

    max_stale_records_percentage: float = 0.0
    """Maximum percentage of records allowed to be stale."""


@dataclass
class ColumnDefinition:
    """Definition of a column in a data contract."""

    name: str
    type: str
    required: bool = True
    description: str = ""
    constraints: Optional[dict] = None

    @classmethod
    def from_dict(cls, data: dict) -> ColumnDefinition:
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            type=data.get("type", "string"),
            required=data.get("required", True),
            description=data.get("description", ""),
            constraints=data.get("constraints"),
        )


@dataclass
class Consumer:
    """Data consumer metadata."""

    name: str
    usage: str = ""
    contact: Optional[str] = None


@dataclass
class Contract:
    """
    Data contract definition.

    Defines expected schema, SLAs, and consumer information for a table.
    """

    name: str
    version: str
    owner: str
    description: str = ""
    schema_columns: list[ColumnDefinition] = field(default_factory=list)
    sla: SLAConfig = field(default_factory=SLAConfig)
    consumers: list[Consumer] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_yaml(cls, yaml_content: str) -> Contract:
        """Load contract from YAML string."""
        data = yaml.safe_load(yaml_content)

        # Parse schema columns
        columns = []
        for col_data in data.get("schema", {}).get("required_columns", []):
            columns.append(ColumnDefinition.from_dict(col_data))

        # Parse SLA
        sla_data = data.get("sla", {})
        sla = SLAConfig(
            freshness_hours=sla_data.get("freshness_hours"),
            quality_threshold=sla_data.get("quality_threshold", 0.99),
            availability_percentage=sla_data.get("availability_percentage", 99.9),
        )

        # Parse consumers
        consumers = []
        for consumer_data in data.get("consumers", []):
            consumers.append(
                Consumer(
                    name=consumer_data.get("name", ""),
                    usage=consumer_data.get("usage", ""),
                    contact=consumer_data.get("contact"),
                )
            )

        return cls(
            name=data.get("name", ""),
            version=data.get("version", "1.0.0"),
            owner=data.get("owner", ""),
            description=data.get("description", ""),
            schema_columns=columns,
            sla=sla,
            consumers=consumers,
        )

    @classmethod
    def from_file(cls, path: Path) -> Contract:
        """Load contract from YAML file."""
        with open(path) as f:
            return cls.from_yaml(f.read())

    def to_dict(self) -> dict:
        """Convert contract to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "owner": self.owner,
            "description": self.description,
            "schema": {
                "required_columns": [
                    {
                        "name": col.name,
                        "type": col.type,
                        "required": col.required,
                        "description": col.description,
                        "constraints": col.constraints or {},
                    }
                    for col in self.schema_columns
                ]
            },
            "sla": {
                "freshness_hours": self.sla.freshness_hours,
                "quality_threshold": self.sla.quality_threshold,
                "availability_percentage": self.sla.availability_percentage,
            },
            "consumers": [
                {"name": c.name, "usage": c.usage, "contact": c.contact}
                for c in self.consumers
            ],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ContractValidator:
    """
    Validates data against contract definitions.

    Checks schema compliance and SLA thresholds.
    """

    def __init__(self, contract: Contract):
        """Initialize validator with a contract."""
        self.contract = contract

    def validate_schema(self, actual_schema: dict) -> tuple[bool, list[str]]:
        """
        Validate actual schema against contract.

        Args:
            actual_schema: Dictionary mapping column_name -> type

        Returns:
            Tuple of (valid, errors)
        """
        errors = []
        actual_columns = set(actual_schema.keys())
        required_columns = {col.name for col in self.contract.schema_columns}

        # Check for missing required columns
        missing = required_columns - actual_columns
        if missing:
            errors.append(f"Missing required columns: {', '.join(missing)}")

        # Check for type mismatches
        for col in self.contract.schema_columns:
            if col.name in actual_schema:
                actual_type = actual_schema[col.name]
                if actual_type != col.type:
                    errors.append(
                        f"Column {col.name}: expected {col.type}, got {actual_type}"
                    )

        return len(errors) == 0, errors

    def validate_sla(self, metrics: dict) -> tuple[bool, list[str]]:
        """
        Validate data metrics against SLA.

        Args:
            metrics: Dictionary with keys like 'quality_score', 'freshness_hours', etc.

        Returns:
            Tuple of (sla_met, violations)
        """
        violations = []

        # Check quality threshold
        if "quality_score" in metrics:
            score = metrics["quality_score"]
            if score < self.contract.sla.quality_threshold:
                violations.append(
                    f"Quality score {score:.2%} below threshold "
                    f"{self.contract.sla.quality_threshold:.2%}"
                )

        # Check freshness
        if self.contract.sla.freshness_hours and "freshness_hours" in metrics:
            freshness = metrics["freshness_hours"]
            if freshness > self.contract.sla.freshness_hours:
                violations.append(
                    f"Data age {freshness}h exceeds freshness SLA "
                    f"{self.contract.sla.freshness_hours}h"
                )

        return len(violations) == 0, violations


class ContractRegistry:
    """
    Registry for managing data contracts.

    Loads, stores, and looks up contracts.
    """

    def __init__(self, contracts_dir: Path = Path("contracts")):
        """Initialize registry."""
        self.contracts_dir = contracts_dir
        self.contracts: dict[str, Contract] = {}
        self._load_all()

    def _load_all(self):
        """Load all contracts from directory."""
        if not self.contracts_dir.exists():
            return

        for yaml_file in self.contracts_dir.glob("*.yaml"):
            try:
                contract = Contract.from_file(yaml_file)
                self.contracts[contract.name] = contract
            except Exception as e:
                print(f"Warning: Could not load contract {yaml_file}: {e}")

    def get(self, name: str) -> Optional[Contract]:
        """Get contract by name."""
        return self.contracts.get(name)

    def list_contracts(self) -> list[str]:
        """List all contract names."""
        return list(self.contracts.keys())

    def add(self, contract: Contract) -> None:
        """Add contract to registry."""
        self.contracts[contract.name] = contract

    def validate_contract(self, name: str, actual_schema: dict) -> tuple[bool, list[str]]:
        """Validate schema against contract."""
        contract = self.get(name)
        if not contract:
            return False, [f"Contract not found: {name}"]

        validator = ContractValidator(contract)
        return validator.validate_schema(actual_schema)
