"""Utility helpers for phlo-testing."""

from __future__ import annotations

from typing import Any

import pandas as pd


def to_dataframe(data: pd.DataFrame | list[dict[str, Any]]) -> pd.DataFrame:
    """Normalize data into a pandas DataFrame."""
    if isinstance(data, pd.DataFrame):
        return data
    return pd.DataFrame(data)


def to_records(data: pd.DataFrame | list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize data into a list of records."""
    df = to_dataframe(data)
    return df.to_dict("records")
