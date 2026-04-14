"""Integration tests for evidence export.

Verifies:
- Evidence pack creation with manifest
- Verification detects tampering
- Pack includes audit chain, signatures, manifest
- CLI export-evidence integration
"""

from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path

from phlo.compliance.audit import InMemoryAuditStore, TamperEvidentAuditSink
from phlo.compliance.evidence import (
    create_evidence_pack,
    verify_evidence_pack,
)
from phlo.compliance.manifest import (
    ComplianceMode,
    DeploymentEnvironment,
    capture_manifest,
)


class TestEvidenceExport:
    """Integration tests for evidence pack export."""

    def test_evidence_pack_roundtrip(self) -> None:
        """Evidence pack can be created, written, and verified."""
        pack = create_evidence_pack(
            created_by="admin@example.com",
            compliance_domain="sox",
            description="Q4 access review evidence",
            audit_records=[{"event": "test", "data": "value"}],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "evidence.zip"
            pack.write_zip(zip_path)

            assert zip_path.exists()

            verification = verify_evidence_pack(zip_path)
            assert verification["valid"] is True
            assert verification["pack_id"] == pack.manifest.pack_id

    def test_evidence_pack_includes_audit_records(self) -> None:
        """Evidence pack includes audit records in export."""
        audit_records = []
        for i in range(10):
            audit_records.append(
                {
                    "event_type": "authorization",
                    "surface": "test-surface",
                    "action": f"action.{i}",
                    "actor_subject": f"user-{i}@example.com",
                    "decision": "allow",
                }
            )

        pack = create_evidence_pack(
            created_by="compliance@example.com",
            compliance_domain="hipaa",
            description="Access certification evidence",
            audit_records=audit_records,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "evidence.zip"
            pack.write_zip(zip_path)

            with zipfile.ZipFile(zip_path, "r") as zf:
                content = zf.read("audit_records.jsonl")
                lines = content.decode().strip().split("\n")
                assert len(lines) == 10

    def test_verify_detects_extra_files(self) -> None:
        """Verification fails when extra files are added to pack."""
        pack = create_evidence_pack(
            created_by="admin@example.com",
            audit_records=[{"test": "data"}],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "evidence.zip"
            pack.write_zip(zip_path)

            with zipfile.ZipFile(zip_path, "a") as zf:
                zf.writestr("extra_file.txt", b"tampered content")

            verification = verify_evidence_pack(zip_path)
            assert verification["valid"] is False
            assert "Unexpected files" in verification.get("error", "")

    def test_verify_detects_missing_files(self) -> None:
        """Verification fails when expected files are missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "evidence.zip"

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                manifest_json = json.dumps(
                    {
                        "pack_id": "test-id",
                        "created_at": "2024-01-01T00:00:00Z",
                        "created_by": "admin@example.com",
                        "compliance_domain": "sox",
                        "description": "Test",
                        "record_count": 1,
                        "file_count": 1,
                        "total_size_bytes": 100,
                        "sha256_hash": "abc123",
                    }
                )
                zf.writestr("manifest.json", manifest_json)

                checksums_json = json.dumps(
                    {
                        "manifest_hash": "abc123",
                        "files": {
                            "audit_records.jsonl": "hash123",
                        },
                    }
                )
                zf.writestr("checksums.json", checksums_json)

            verification = verify_evidence_pack(zip_path)
            assert verification["valid"] is False

    def test_evidence_pack_with_system_manifest(self) -> None:
        """Evidence pack includes system manifest data."""
        from phlo.compliance.manifest import SecurityConfiguration

        security = SecurityConfiguration(
            compliance_mode=ComplianceMode.REGULATED,
            regulated=True,
            tamper_evident_audit=True,
            electronic_signatures=True,
            access_governance=True,
        )

        manifest = capture_manifest(
            phlo_version="1.0.0",
            environment=DeploymentEnvironment.PRODUCTION,
            security=security,
        )

        manifest_data = {
            "manifest_id": manifest.manifest_id,
            "environment": manifest.environment.value,
            "components": [
                {
                    "name": c.name,
                    "version": c.version,
                    "type": c.type,
                }
                for c in manifest.components
            ],
        }

        pack = create_evidence_pack(
            created_by="system@example.com",
            compliance_domain="sox",
            description="System manifest evidence",
            manifest_data=manifest_data,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "evidence.zip"
            pack.write_zip(zip_path)

            with zipfile.ZipFile(zip_path, "r") as zf:
                manifest_content = zf.read("system_manifest.json")
                loaded = json.loads(manifest_content)
                assert "manifest_id" in loaded
                assert loaded["environment"] == "production"

    def test_evidence_pack_with_signature_records(self) -> None:
        """Evidence pack includes signature records."""
        sig_records = [
            {
                "signer_subject": "alice@example.com",
                "meaning": "approved",
                "record_type": "dataset",
                "record_id": f"dataset-{i}",
                "signature_hash": f"hash-{i}",
            }
            for i in range(5)
        ]

        pack = create_evidence_pack(
            created_by="compliance@example.com",
            signatures=sig_records,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "evidence.zip"
            pack.write_zip(zip_path)

            with zipfile.ZipFile(zip_path, "r") as zf:
                sigs_content = zf.read("signatures.jsonl")
                lines = sigs_content.decode().strip().split("\n")
                assert len(lines) == 5

    def test_cli_export_evidence_command(self) -> None:
        """CLI export-evidence command creates valid pack."""
        from click.testing import CliRunner

        from phlo.cli.commands.compliance import export_evidence

        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "evidence.zip"

            result = runner.invoke(
                export_evidence,
                [
                    "--output",
                    str(output_path),
                    "--created-by",
                    "cli-user@example.com",
                    "--domain",
                    "pci",
                    "--description",
                    "PCI compliance evidence",
                ],
            )

            assert result.exit_code == 0
            assert output_path.exists()

            verification = verify_evidence_pack(output_path)
            assert verification["valid"] is True

    def test_cli_verify_evidence_command(self) -> None:
        """CLI verify-evidence command validates packs correctly."""
        from click.testing import CliRunner

        from phlo.cli.commands.compliance import verify_evidence

        pack = create_evidence_pack(
            created_by="admin@example.com",
        )

        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "evidence.zip"
            pack.write_zip(output_path)

            result = runner.invoke(
                verify_evidence,
                [str(output_path)],
            )

            assert result.exit_code == 0
            assert "valid" in result.output.lower()

    def test_evidence_pack_contains_correct_metadata(self) -> None:
        """Evidence pack contains correct metadata from inputs."""
        audit_records = [{"event": "test", "data": "value"}]

        pack = create_evidence_pack(
            created_by="admin@example.com",
            compliance_domain="sox",
            description="Test evidence pack",
            audit_records=audit_records,
        )

        assert pack.manifest.created_by == "admin@example.com"
        assert pack.manifest.compliance_domain == "sox"
        assert pack.manifest.description == "Test evidence pack"
        assert pack.manifest.record_count == 1
        assert pack.manifest.file_count > 0

    def test_full_compliance_pipeline_integration(self) -> None:
        """End-to-end: create audit events, sign, export, verify."""
        store = InMemoryAuditStore()
        sink = TamperEvidentAuditSink(store)

        for i in range(5):
            from phlo.audit.events import CanonicalAuditEvent

            event = CanonicalAuditEvent(
                event_type="authorization",
                surface="phlo-api",
                action="dataset.read",
                resource_type="dataset",
                resource_id=f"dataset-{i}",
                actor_subject="alice@example.com",
                actor_type="user",
                actor_roles=("data_read",),
                authentication_source="proxy",
                decision="allow",
                reason_code="",
                policy_id=None,
                request_id=f"req-{i}",
            )
            sink.write(event)

        audit_records = []
        for record in store.query("phlo-api", limit=100):
            audit_records.append(record.event.to_dict())

        pack = create_evidence_pack(
            created_by="compliance@example.com",
            compliance_domain="sox",
            description="Full pipeline test",
            audit_records=audit_records,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "full_evidence.zip"
            pack.write_zip(zip_path)

            verification = verify_evidence_pack(zip_path)
            assert verification["valid"] is True
            assert verification["record_count"] == 5

    def test_evidence_pack_multiple_compliance_domains(self) -> None:
        """Evidence packs can specify different compliance domains."""
        for domain in ["sox", "hipaa", "pci", "gdpr"]:
            pack = create_evidence_pack(
                created_by="admin@example.com",
                compliance_domain=domain,
            )

            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = Path(tmpdir) / f"evidence_{domain}.zip"
                pack.write_zip(zip_path)

                verification = verify_evidence_pack(zip_path)
                assert verification["valid"] is True
