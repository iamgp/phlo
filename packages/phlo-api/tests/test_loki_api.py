"""Tests for Loki response normalization and URL override rejection."""

from __future__ import annotations

import json

import pytest
from fastapi import HTTPException

from phlo_api.observatory_api.loki import (
    build_log_query,
    parse_loki_response,
    reject_request_loki_url,
    resolve_loki_url,
)


def test_build_log_query_matches_dagster_run_id_in_plain_container_logs() -> None:
    """Run correlation must work before JSON parsing structured application logs."""
    assert build_log_query(run_id="run-123") == ('{container=~".+"} |= "run-123" | json')


def test_parse_loki_response_emits_function_and_legacy_fn_metadata() -> None:
    response = {
        "data": {
            "result": [
                {
                    "stream": {},
                    "values": [
                        [
                            "1700000000000000000",
                            json.dumps(
                                {
                                    "level": "info",
                                    "message": "hello",
                                    "function": "run_step",
                                }
                            ),
                        ]
                    ],
                }
            ]
        }
    }

    entries = parse_loki_response(response)

    assert entries[0].metadata["function"] == "run_step"
    assert entries[0].metadata["fn"] == "run_step"


def test_parse_loki_response_reads_legacy_fn_metadata() -> None:
    response = {
        "data": {
            "result": [
                {
                    "stream": {},
                    "values": [
                        [
                            "1700000000000000000",
                            json.dumps({"level": "info", "message": "hello", "fn": "run_step"}),
                        ]
                    ],
                }
            ]
        }
    }

    entries = parse_loki_response(response)

    assert entries[0].metadata["function"] == "run_step"
    assert entries[0].metadata["fn"] == "run_step"


def test_reject_request_loki_url_override() -> None:
    reject_request_loki_url(None)

    with pytest.raises(HTTPException) as exc:
        reject_request_loki_url("http://169.254.169.254/latest/meta-data/#")

    assert exc.value.status_code == 422
    assert exc.value.detail["error"] == "loki_url_override_not_allowed"


def test_resolve_loki_url_uses_server_configuration_only(monkeypatch) -> None:
    monkeypatch.setattr(
        "phlo_api.observatory_api.loki.resolve_url",
        lambda url, *, port_env_var=None: url,
    )
    monkeypatch.setattr(
        "phlo_api.observatory_api.loki.project_env_value",
        lambda key, default=None: "http://loki.internal:3100" if key == "LOKI_URL" else default,
    )

    assert resolve_loki_url() == "http://loki.internal:3100"
    with pytest.raises(TypeError):
        resolve_loki_url("http://attacker.example")  # type: ignore[call-arg]
