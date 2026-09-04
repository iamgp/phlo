"""Phlo-owned conformance worker.

This module is executed STANDALONE by the disposable worker interpreter
inside the candidate's isolated installation; it must never import phlo
or anything outside the standard library, because the candidate's
environment contains only the candidate wheel (and its declared
dependencies). It loads ONLY candidate-owned entry points from the one
suite-configured group, runs the frozen Phlo-owned cases for the suite,
and writes a structured result document for the controller.

The controller never imports candidate code (ADR 0053 concern 4 /
issue #856 isolation boundary): all candidate execution happens here.

Case logic is Phlo-owned and frozen by the suite definition in
``suites.py``; providers never supply test logic. Cases assert the
``query_engine.v1`` contract structurally (duck typing), because the
worker cannot import Phlo's protocol classes.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import sys
import traceback
from pathlib import Path
from typing import Any

# --- Frozen case implementations for query_engine.v1 -----------------------
# These names and semantics must stay in lockstep with the suite
# definition (SuiteDefinition.cases in suites.py).


def _case_spec_identity(spec: Any) -> str:
    name = getattr(spec, "name", None)
    provider = getattr(spec, "provider", None)
    if not isinstance(name, str) or not name:
        raise AssertionError(f"spec {spec!r} must expose a non-empty string name")
    if provider is None:
        raise AssertionError(f"spec {name!r} must expose a provider object")
    return f"spec {name!r} exposes a provider"


def _rows_of(result: Any) -> list[Any]:
    if result is None:
        raise AssertionError("execute() returned None; expected provider-native results")
    fetchall = getattr(result, "fetchall", None)
    if callable(fetchall):
        rows = fetchall()
        if not isinstance(rows, list):
            rows = list(rows)
        return list(rows)
    if isinstance(result, (list, tuple)):
        return list(result)
    return []


def _case_execute_literal_select(spec: Any) -> str:
    result = spec.provider.execute("SELECT 1 AS one")
    rows = _rows_of(result)
    if not rows:
        raise AssertionError("execute('SELECT 1 AS one') returned no rows")
    return f"literal select returned {len(rows)} row(s)"


def _case_execute_error_surfaces(spec: Any) -> str:
    try:
        spec.provider.execute("THIS IS NOT VALID SQL")
    except Exception:
        return "invalid SQL raised an exception instead of being swallowed"
    raise AssertionError("execute() swallowed invalid SQL; engines must surface errors")


def _preview_page(spec: Any, relation: str, *, limit: int, offset: int) -> Any:
    return spec.provider.preview(relation, limit=limit, offset=offset)


def _assert_page_shape(page: Any, limit: int) -> list[dict[str, Any]]:
    columns = getattr(page, "columns", None)
    column_types = getattr(page, "column_types", None)
    rows = getattr(page, "rows", None)
    if not isinstance(columns, list) or not columns or not all(isinstance(c, str) for c in columns):
        raise AssertionError("preview() must expose columns as a non-empty list of str")
    if not isinstance(column_types, list) or not all(isinstance(t, str) for t in column_types):
        raise AssertionError("preview() must expose column_types as a list of str")
    if len(column_types) != len(columns):
        raise AssertionError("preview() column_types must align with columns")
    if not isinstance(rows, list):
        raise AssertionError("preview() must expose rows as a list")
    if len(rows) > limit:
        raise AssertionError(f"preview() returned {len(rows)} rows for limit {limit}")
    for row in rows:
        if not isinstance(row, dict):
            raise AssertionError("preview() rows must be dicts keyed by column name")
        for column in columns:
            if column not in row:
                raise AssertionError(f"preview() row is missing column {column!r}")
    return rows


def _case_preview_bounded_page(spec: Any) -> str:
    spec.provider.execute("CREATE TABLE conformance_cases (id INTEGER, label TEXT)")
    for index in range(3):
        spec.provider.execute(f"INSERT INTO conformance_cases VALUES ({index}, 'row-{index}')")
    page = _preview_page(spec, "conformance_cases", limit=2, offset=0)
    rows = _assert_page_shape(page, limit=2)
    if len(rows) != 2:
        raise AssertionError(f"expected exactly 2 rows on the first page, got {len(rows)}")
    return f"bounded page returned {len(rows)} dict rows with typed columns"


def _case_preview_offset_pages(spec: Any) -> str:
    first = _assert_page_shape(_preview_page(spec, "conformance_cases", limit=2, offset=0), limit=2)
    second = _assert_page_shape(
        _preview_page(spec, "conformance_cases", limit=2, offset=2), limit=2
    )
    if first and second and first[0] == second[0]:
        raise AssertionError("offset=2 returned the same first row as offset=0")
    return "offset paging skips rows deterministically"


#: Case registry: (name, callable(spec) -> detail). Order is the run order.
CASES: list[tuple[str, Any]] = [
    ("spec_identity", _case_spec_identity),
    ("execute_literal_select", _case_execute_literal_select),
    ("execute_error_surfaces", _case_execute_error_surfaces),
    ("preview_bounded_page", _case_preview_bounded_page),
    ("preview_offset_pages", _case_preview_offset_pages),
]


def load_specs(entry_point_group: str) -> tuple[list[Any], list[str]]:
    """Load ONLY candidate-owned entry points from the suite's group.

    The worker never touches any other entry-point group: in the
    disposable environment every entry point in this group is
    candidate-owned by construction.
    """
    entry_points = importlib.metadata.entry_points()
    select = getattr(entry_points, "select", None)
    if callable(select):
        selected = list(select(group=entry_point_group))
    else:  # pragma: no cover - pre-3.10 fallback
        selected = list(entry_points.get(entry_point_group, []))  # type: ignore[union-attr]

    specs: list[Any] = []
    loaded: list[str] = []
    for entry_point in selected:
        try:
            plugin = entry_point.load()
            instance = plugin() if isinstance(plugin, type) else plugin
            specs.extend(list(instance.get_query_engines()))
            loaded.append(entry_point.name)
        except Exception:
            specs.append(_BrokenSpec(entry_point.name, traceback.format_exc()))
    return specs, loaded


class _BrokenSpec:
    """Stands in for a candidate plugin that failed to load, so the
    failure surfaces as a failed case instead of a crashed worker."""

    def __init__(self, name: str, error: str) -> None:
        self.name = name
        self.provider = _BrokenProvider(error)


class _BrokenProvider:
    def __init__(self, error: str) -> None:
        self._error = error

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        raise AssertionError(f"candidate plugin failed to load: {self._error}")

    def preview(self, *args: Any, **kwargs: Any) -> Any:
        raise AssertionError(f"candidate plugin failed to load: {self._error}")


def run_cases(spec: Any) -> list[dict[str, Any]]:
    results = []
    for case_name, case_callable in CASES:
        try:
            detail = case_callable(spec)
            results.append({"name": case_name, "passed": True, "detail": str(detail)})
        except Exception as exc:
            results.append(
                {
                    "name": case_name,
                    "passed": False,
                    "detail": f"{type(exc).__name__}: {exc}",
                }
            )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Phlo conformance worker (candidate-side).")
    parser.add_argument("--entry-point-group", required=True)
    parser.add_argument("--suite", required=True)
    parser.add_argument("--output", required=True)
    arguments = parser.parse_args()

    specs, loaded = load_specs(arguments.entry_point_group)
    case_results: list[dict[str, Any]] = []
    for spec in specs:
        spec_name = getattr(spec, "name", "<unnamed>")
        for case_result in run_cases(spec):
            case_results.append({"spec": spec_name, **case_result})

    document = {
        "suite": arguments.suite,
        "entry_point_group": arguments.entry_point_group,
        "loaded_entry_points": loaded,
        "specs": [getattr(spec, "name", "<unnamed>") for spec in specs],
        "cases": case_results,
        "passed": bool(case_results) and all(case["passed"] for case in case_results),
    }
    with Path(arguments.output).open("w", encoding="utf-8") as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
