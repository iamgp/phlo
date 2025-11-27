"""
Data contracts module for enforcing SLAs and schema governance.

Provides:
- Contract definition and validation
- Schema evolution tracking
- Consumer notification system
- Breaking change detection
"""

from phlo.contracts.schema import Contract, ContractValidator, SLAConfig
from phlo.contracts.evolution import SchemaEvolution, ChangeClassification
from phlo.contracts.notifications import NotificationConfig, NotificationManager

__all__ = [
    "Contract",
    "ContractValidator",
    "SLAConfig",
    "SchemaEvolution",
    "ChangeClassification",
    "NotificationConfig",
    "NotificationManager",
]
