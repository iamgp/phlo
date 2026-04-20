"""Tamper-evident audit sealing and sink.

Provides HMAC-keyed hash-chained audit records for tamper-evident audit trails.
The HMAC key prevents an attacker with database access from recalculating the
chain after modifying records.
"""

from __future__ import annotations

import hashlib
import hmac as _hmac
import json
import os
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from phlo.audit.events import CanonicalAuditEvent

GENESIS_HASH = "0" * 64
PHLO_AUDIT_HMAC_KEY_ENV = "PHLO_AUDIT_HMAC_KEY"


def _get_hmac_key() -> bytes:
    """Return the HMAC key from the environment, or a default for dev/test."""
    key = os.environ.get(PHLO_AUDIT_HMAC_KEY_ENV, "")
    if key:
        return key.encode()
    return b"phlo-dev-audit-key"


def compute_record_hash(
    event: CanonicalAuditEvent,
    sequence_number: int,
    previous_hash: str,
    hmac_key: bytes | None = None,
) -> str:
    """Compute the tamper-evident HMAC for a sealed audit record."""
    if hmac_key is None:
        hmac_key = _get_hmac_key()
    event_dict = event.to_dict()
    payload = f"{sequence_number}:{json.dumps(event_dict, sort_keys=True)}:{previous_hash}"
    return _hmac.new(hmac_key, payload.encode(), hashlib.sha256).hexdigest()


@dataclass(frozen=True)
class SealedAuditRecord:
    """Sealed audit record with HMAC hash chain.

    Each record contains the original audit event plus chain metadata
    that allows verification of the chain's integrity. The record hash
    is an HMAC-SHA256 keyed with a secret so that an attacker cannot
    recompute the chain without the key.
    """

    sequence_number: int
    """Monotonically increasing sequence number per surface."""

    event: CanonicalAuditEvent
    """The original audit event."""

    previous_hash: str
    """HMAC hash of the previous sealed record. Genesis is all zeros."""

    record_hash: str
    """HMAC-SHA256 of (sequence_number, event.to_dict(), previous_hash)."""

    sealed_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    """ISO 8601 timestamp when the record was sealed."""

    @classmethod
    def seal(
        cls,
        event: CanonicalAuditEvent,
        sequence_number: int,
        previous_hash: str,
        hmac_key: bytes | None = None,
    ) -> SealedAuditRecord:
        """Create a sealed audit record.

        Args:
            event: The audit event to seal.
            sequence_number: Monotonically increasing sequence number.
            previous_hash: Hash of the previous record, or GENESIS_HASH for first.
            hmac_key: Secret key for HMAC. Uses env default if not provided.

        Returns:
            SealedAuditRecord with computed record_hash.
        """
        record_hash = compute_record_hash(
            event,
            sequence_number,
            previous_hash,
            hmac_key=hmac_key,
        )

        return cls(
            sequence_number=sequence_number,
            event=event,
            previous_hash=previous_hash,
            record_hash=record_hash,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "sequence_number": self.sequence_number,
            "sealed_at": self.sealed_at,
            "previous_hash": self.previous_hash,
            "record_hash": self.record_hash,
            "event": self.event.to_dict(),
        }


class TamperEvidentAuditSink:
    """Audit sink that seals events with hash chaining.

    Wraps an AuditStore and maintains per-surface sequence counters
    and last hashes for chain integrity.

    Thread-safe via lock per surface.
    """

    def __init__(self, store: AuditStore, hmac_key: bytes | None = None) -> None:
        """Initialize the tamper-evident sink.

        Args:
            store: The AuditStore to delegate to.
            hmac_key: Secret key for HMAC sealing. Uses env default if not provided.
        """
        self._store = store
        self._hmac_key = hmac_key or _get_hmac_key()
        self._surface_locks: dict[str, threading.Lock] = {}
        self._surface_locks_guard = threading.Lock()
        self._surface_state: dict[str, tuple[int, str]] = {}
        self._state_guard = threading.Lock()

    def _get_surface_lock(self, surface: str) -> threading.Lock:
        """Get or create a lock for a surface."""
        with self._surface_locks_guard:
            if surface not in self._surface_locks:
                self._surface_locks[surface] = threading.Lock()
            return self._surface_locks[surface]

    def _get_surface_state(self, surface: str) -> tuple[int, str]:
        """Get the sequence number and last hash for a surface.

        Initializes from store if not cached.
        """
        with self._state_guard:
            if surface not in self._surface_state:
                last_record = self._store.get_last(surface)
                if last_record is None:
                    self._surface_state[surface] = (0, GENESIS_HASH)
                else:
                    self._surface_state[surface] = (
                        last_record.sequence_number,
                        last_record.record_hash,
                    )
            return self._surface_state[surface]

    def write(self, event: CanonicalAuditEvent) -> None:
        """Seal and write an audit event.

        Args:
            event: The audit event to seal and write.
        """
        surface = event.surface or "unknown"
        lock = self._get_surface_lock(surface)

        with lock:
            seq, prev_hash = self._get_surface_state(surface)
            new_seq = seq + 1

            sealed = SealedAuditRecord.seal(event, new_seq, prev_hash, hmac_key=self._hmac_key)

            self._store.append(sealed)

            with self._state_guard:
                self._surface_state[surface] = (new_seq, sealed.record_hash)


class AuditStore:
    """Protocol for audit storage backends."""

    def append(self, record: SealedAuditRecord) -> None:
        """Append a sealed record to the store.

        Args:
            record: The sealed audit record to append.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError

    def get_last(self, surface: str) -> SealedAuditRecord | None:
        """Get the last sealed record for a surface.

        Args:
            surface: The surface name.

        Returns:
            The last sealed record, or None if no records exist.
        """
        raise NotImplementedError

    def query(
        self,
        surface: str,
        after: int | None = None,
        before: int | None = None,
        limit: int = 1000,
    ) -> list[SealedAuditRecord]:
        """Query sealed records for a surface.

        Args:
            surface: The surface name.
            after: Sequence number lower bound (exclusive).
            before: Sequence number upper bound (exclusive).
            limit: Maximum number of records to return.

        Returns:
            List of matching sealed records.
        """
        raise NotImplementedError

    def verify_chain(
        self,
        surface: str,
        hmac_key: bytes | None = None,
    ) -> ChainVerificationResult:
        """Verify the integrity of the chain for a surface.

        Args:
            surface: The surface name.
            hmac_key: Secret key for HMAC verification. Uses env default if not provided.

        Returns:
            ChainVerificationResult with pass/fail and details.
        """
        raise NotImplementedError


@dataclass(frozen=True)
class ChainVerificationResult:
    """Result of a chain verification check."""

    valid: bool
    """Whether the chain is valid."""

    surface: str
    """The surface that was verified."""

    total_records: int
    """Total number of records in the chain."""

    first_invalid_sequence: int | None = None
    """Sequence number of first invalid record, if any."""

    error_message: str | None = None
    """Error message if verification failed."""

    verified_hashes: list[str] = field(default_factory=list)
    """List of verified record hashes in order."""
