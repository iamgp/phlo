"""Tests for Loki response normalization."""

from __future__ import annotations

import json

from phlo_api.observatory_api.loki import parse_loki_response


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
