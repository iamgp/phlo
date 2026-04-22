"""Evidence pack creation for compliance auditing.

Evidence packs bundle audit records, signatures, manifests, and other
compliance artifacts into a tamper-evident package suitable for
submission to auditors or regulators.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


@dataclass(frozen=True, kw_only=True)
class EvidenceManifest:
    """Manifest describing the contents of an evidence pack."""

    pack_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    created_by: str
    compliance_domain: str | None = None
    description: str | None = None
    record_count: int = 0
    file_count: int = 0
    total_size_bytes: int = 0
    sha256_hash: str = ""


@dataclass
class EvidencePack:
    """An evidence pack containing compliance artifacts.

    Evidence packs are used to submit compliance evidence to auditors.
    They contain a manifest and one or more files with audit records,
    signatures, and other compliance artifacts.
    """

    manifest: EvidenceManifest
    files: dict[str, bytes]

    def write_zip(self, output_path: Path) -> None:
        """Write the evidence pack as a ZIP file.

        Args:
            output_path: Path to write the ZIP file.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            manifest_json = json.dumps(
                {
                    "pack_id": self.manifest.pack_id,
                    "created_at": self.manifest.created_at,
                    "created_by": self.manifest.created_by,
                    "compliance_domain": self.manifest.compliance_domain,
                    "description": self.manifest.description,
                    "record_count": self.manifest.record_count,
                    "file_count": self.manifest.file_count,
                    "total_size_bytes": self.manifest.total_size_bytes,
                    "sha256_hash": self.manifest.sha256_hash,
                },
                sort_keys=True,
            )
            zf.writestr("manifest.json", manifest_json)

            for filename, content in self.files.items():
                zf.writestr(filename, content)

            manifest_sha = hashlib.sha256(manifest_json.encode()).hexdigest()
            checksum_json = json.dumps(
                {
                    "manifest_hash": manifest_sha,
                    "files": {
                        name: hashlib.sha256(content).hexdigest()
                        for name, content in self.files.items()
                    },
                },
                sort_keys=True,
            )
            zf.writestr("checksums.json", checksum_json)


def create_evidence_pack(
    created_by: str,
    compliance_domain: str | None = None,
    description: str | None = None,
    audit_records: list[dict[str, Any]] | None = None,
    signatures: list[dict[str, Any]] | None = None,
    manifest_data: dict[str, Any] | None = None,
) -> EvidencePack:
    """Create an evidence pack with the given contents.

    Args:
        created_by: Subject who created the pack.
        compliance_domain: Compliance domain (e.g., "sox", "hipaa", "pci").
        description: Description of the evidence pack.
        audit_records: List of audit record dicts to include.
        signatures: List of signature record dicts to include.
        manifest_data: System manifest data to include.

    Returns:
        An EvidencePack ready to be written.
    """
    files: dict[str, bytes] = {}

    if audit_records:
        audit_json = "\n".join(json.dumps(r, sort_keys=True) for r in audit_records)
        files["audit_records.jsonl"] = audit_json.encode()

    if signatures:
        sig_json = "\n".join(json.dumps(s, sort_keys=True) for s in signatures)
        files["signatures.jsonl"] = sig_json.encode()

    if manifest_data:
        manifest_json = json.dumps(manifest_data, sort_keys=True)
        files["system_manifest.json"] = manifest_json.encode()

    total_size = sum(len(v) for v in files.values())

    pack_manifest = EvidenceManifest(
        created_by=created_by,
        compliance_domain=compliance_domain,
        description=description,
        record_count=len(audit_records) if audit_records else 0,
        file_count=len(files),
        total_size_bytes=total_size,
    )

    return EvidencePack(manifest=pack_manifest, files=files)


def verify_evidence_pack(zip_path: Path) -> dict[str, Any]:
    """Verify the integrity of an evidence pack ZIP file.

    Args:
        zip_path: Path to the evidence pack ZIP file.

    Returns:
        Verification result with details.
    """
    if not zip_path.exists():
        return {"valid": False, "error": "File not found"}

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            if "manifest.json" not in zf.namelist():
                return {"valid": False, "error": "Missing manifest.json"}

            if "checksums.json" not in zf.namelist():
                return {"valid": False, "error": "Missing checksums.json"}

            manifest_data = json.loads(zf.read("manifest.json"))
            checksums_data = json.loads(zf.read("checksums.json"))

            actual_manifest_hash = hashlib.sha256(zf.read("manifest.json")).hexdigest()
            if actual_manifest_hash != checksums_data.get("manifest_hash"):
                return {"valid": False, "error": "Manifest hash mismatch"}

            expected_files = set(checksums_data.get("files", {}).keys())
            actual_files = set(zf.namelist()) - {"manifest.json", "checksums.json"}
            if expected_files != actual_files:
                extra = actual_files - expected_files
                missing = expected_files - actual_files
                if extra:
                    return {"valid": False, "error": f"Unexpected files in pack: {extra}"}
                if missing:
                    return {"valid": False, "error": f"Missing files from pack: {missing}"}

            for filename, expected_hash in checksums_data.get("files", {}).items():
                if filename not in zf.namelist():
                    return {"valid": False, "error": f"Missing file: {filename}"}
                actual_hash = hashlib.sha256(zf.read(filename)).hexdigest()
                if actual_hash != expected_hash:
                    return {"valid": False, "error": f"Hash mismatch for {filename}"}

        return {
            "valid": True,
            "pack_id": manifest_data.get("pack_id"),
            "created_at": manifest_data.get("created_at"),
            "file_count": manifest_data.get("file_count", 0),
            "record_count": manifest_data.get("record_count", 0),
        }

    except zipfile.BadZipFile:
        return {"valid": False, "error": "Invalid ZIP file"}
    except json.JSONDecodeError:
        return {"valid": False, "error": "Invalid JSON in pack"}
    except Exception as e:
        return {"valid": False, "error": str(e)}
