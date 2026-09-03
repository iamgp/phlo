"""Compliance audit subsystem.

Provides tamper-evident audit storage with hash chaining.
"""

from __future__ import annotations

from phlo.compliance.audit.export import export_jsonl, verify_and_export
from phlo.compliance.audit.sealed import (
    GENESIS_HASH,
    AuditStore,
    ChainVerificationResult,
    SealedAuditRecord,
    TamperEvidentAuditSink,
)
from phlo.compliance.audit.store import InMemoryAuditStore, PostgresAuditStore

__all__ = [
    "AuditStore",
    "ChainVerificationResult",
    "GENESIS_HASH",
    "InMemoryAuditStore",
    "PostgresAuditStore",
    "SealedAuditRecord",
    "TamperEvidentAuditSink",
    "export_jsonl",
    "verify_and_export",
]
