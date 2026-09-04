"""Observatory package-install preflight wiring (issue #857).

The Observatory mutation must receive the same pure preflight verdict as
the CLI before any installer subprocess runs; rejected candidates never
reach ``_run_python_package_install``. Patching the shared preflight
module attribute proves both mutation surfaces call one decision
(mechanical CLI/API drift prevention).
"""

from __future__ import annotations

from pathlib import Path

from phlo.plugins import preflight
from phlo_api.observatory_api import package_install
from security_test_support import authenticated_client


def _admin_env(monkeypatch, project_root: Path) -> None:
    monkeypatch.setenv("PHLO_PROJECT_PATH", str(project_root))
    monkeypatch.setenv(
        "PHLO_API_TOKENS",
        '{"admin-token":{"subject":"admin","scopes":["admin"]}}',
    )


def _registry_payload():
    return {
        "plugins": {
            "preflight-fixture": {
                "type": "resource",
                "package": "phlo-preflight-fixture",
                "version": "0.1.0",
                "description": "Preflight fixture",
                "author": "Preflight Fixture Author",
                "tags": ["fixture"],
            }
        }
    }


def test_rejected_candidate_never_reaches_the_installer(monkeypatch, tmp_path: Path) -> None:
    """A project demanding a conformance-tested query engine rejects the
    unevidenced candidate with 400 before any subprocess runs."""
    _admin_env(monkeypatch, tmp_path)
    (tmp_path / "phlo.yaml").write_text(
        "capabilities:\n  defaults:\n    query_engine: preflight-fixture\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(package_install, "get_registry_data", _registry_payload)

    def forbidden(package_spec: str) -> tuple[bool, str]:
        raise AssertionError("installer must not run for a rejected candidate")

    monkeypatch.setattr(package_install, "_run_python_package_install", forbidden)

    response = authenticated_client("admin").post(
        "/api/observatory/packages/install",
        json={"package_name": "preflight-fixture"},
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 400
    assert "preflight" in response.json()["detail"].lower()


def test_shared_preflight_decides_before_the_mutation(monkeypatch, tmp_path: Path) -> None:
    """Order and drift proof: the Observatory path calls the same pure
    preflight module the CLI calls, strictly before the installer."""
    _admin_env(monkeypatch, tmp_path)
    monkeypatch.setattr(package_install, "get_registry_data", _registry_payload)
    monkeypatch.setattr(package_install, "_load_services", lambda: [])

    installed: list[str] = []
    monkeypatch.setattr(
        package_install,
        "_run_python_package_install",
        lambda package_spec: installed.append(package_spec) or (True, "installed"),
    )

    order: list[str] = []
    real_evaluate = preflight.evaluate_install_preflight

    def recording_evaluate(**kwargs):
        order.append("preflight")
        return real_evaluate(**kwargs)

    monkeypatch.setattr(preflight, "evaluate_install_preflight", recording_evaluate)

    response = authenticated_client("admin").post(
        "/api/observatory/packages/install",
        json={"package_name": "preflight-fixture"},
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    assert order == ["preflight"]
    assert installed == ["phlo-preflight-fixture==0.1.0"]


def test_override_is_explicit_tier_preserving(monkeypatch, tmp_path: Path) -> None:
    """The request override installs a community candidate; the tier never
    changes and the response records the overridden rule."""
    _admin_env(monkeypatch, tmp_path)
    (tmp_path / "phlo.yaml").write_text(
        "capabilities:\n  defaults:\n    query_engine: preflight-fixture\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(package_install, "get_registry_data", _registry_payload)
    monkeypatch.setattr(package_install, "_load_services", lambda: [])

    installed: list[str] = []
    monkeypatch.setattr(
        package_install,
        "_run_python_package_install",
        lambda package_spec: installed.append(package_spec) or (True, "installed"),
    )

    response = authenticated_client("admin").post(
        "/api/observatory/packages/install",
        json={
            "package_name": "preflight-fixture",
            "allow_community": True,
            "override_reason": "team decision, recorded",
        },
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    assert installed == ["phlo-preflight-fixture==0.1.0"]
    assert "remains tier community" in response.json()["message"]
    assert "min_tier:query_engine" in response.json()["message"]


def test_override_without_reason_is_refused_before_the_installer(
    monkeypatch, tmp_path: Path
) -> None:
    _admin_env(monkeypatch, tmp_path)
    (tmp_path / "phlo.yaml").write_text(
        "capabilities:\n  defaults:\n    query_engine: preflight-fixture\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(package_install, "get_registry_data", _registry_payload)

    def forbidden(package_spec: str) -> tuple[bool, str]:
        raise AssertionError("installer must not run for a rejected candidate")

    monkeypatch.setattr(package_install, "_run_python_package_install", forbidden)

    response = authenticated_client("admin").post(
        "/api/observatory/packages/install",
        json={"package_name": "preflight-fixture", "allow_community": True},
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 400


def test_evidence_env_loads_into_the_shared_decision(monkeypatch, tmp_path: Path) -> None:
    """$PHLO_CONFORMANCE_EVIDENCE documents enter the same pure decision."""
    _admin_env(monkeypatch, tmp_path)
    monkeypatch.setattr(package_install, "get_registry_data", _registry_payload)
    monkeypatch.setattr(package_install, "_load_services", lambda: [])
    monkeypatch.setattr(
        package_install,
        "_run_python_package_install",
        lambda package_spec: (True, "installed"),
    )

    evidence = tmp_path / "evidence.json"
    evidence.write_text(
        '{"subject": {"package": "phlo-preflight-fixture", "version": "0.1.0",'
        ' "digest": "sha256:' + "00" * 32 + '"}, "tracer": "query_engine.v1",'
        ' "result": "pass", "evidence_refs": ["evidence:x"],'
        ' "executed_by": "phlo-conformance", "run_at": "2026-09-01T00:00:00Z",'
        ' "expires_at": "2026-12-01T00:00:00Z"}',
        encoding="utf-8",
    )
    monkeypatch.setenv("PHLO_CONFORMANCE_EVIDENCE", str(evidence))

    seen: dict[str, object] = {}
    real_evaluate = preflight.evaluate_install_preflight

    def spy(**kwargs):
        seen["records"] = kwargs.get("conformance_results")
        seen["legacy_verified"] = kwargs.get("legacy_verified")
        return real_evaluate(**kwargs)

    monkeypatch.setattr(preflight, "evaluate_install_preflight", spy)

    response = authenticated_client("admin").post(
        "/api/observatory/packages/install",
        json={"package_name": "preflight-fixture"},
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    records = seen["records"]
    assert records is not None and len(records) == 1
    assert records[0].tracer == "query_engine.v1"
    assert seen["legacy_verified"] is False
