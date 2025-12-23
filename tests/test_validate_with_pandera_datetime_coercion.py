from __future__ import annotations

import logging
from types import SimpleNamespace

import pandas as pd
from pandera.typing import Series
from phlo_dlt.dlt_helpers import validate_with_pandera

from phlo.schemas import PhloSchema


class ExampleSchema(PhloSchema):
    created_at: Series[pd.Timestamp]
    name: Series[str]


def test_validate_with_pandera_only_coerces_datetime_columns(monkeypatch) -> None:
    captured: dict[str, pd.DataFrame] = {}

    def _validate(cls, df: pd.DataFrame, *args, **kwargs):  # noqa: ANN001,ANN002,ANN003
        captured["df"] = df.copy()
        return df

    monkeypatch.setattr(ExampleSchema, "validate", classmethod(_validate))

    context = SimpleNamespace(log=logging.getLogger("phlo.tests.validate_with_pandera"))
    data = [{"created_at": "2024-01-01T00:00:00Z", "name": "2024-01-02"}]

    assert validate_with_pandera(context, data, ExampleSchema) is True

    df = captured["df"]
    assert pd.api.types.is_datetime64_any_dtype(df["created_at"])
    assert pd.api.types.is_string_dtype(df["name"]) or pd.api.types.is_object_dtype(df["name"])
    assert df["name"].iloc[0] == "2024-01-02"
