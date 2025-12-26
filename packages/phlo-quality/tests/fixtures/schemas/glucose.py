"""Fixture glucose schemas for CLI tests."""

from pandera.pandas import Field
from phlo_quality.schemas import PhloSchema


class RawGlucoseEntries(PhloSchema):
    """Raw glucose entries schema fixture."""

    _id: str = Field(unique=True)
    sgv: int = Field(ge=0)
    date: int = Field(ge=0)


class FactGlucoseReadings(PhloSchema):
    """Fact glucose readings schema fixture."""

    entry_id: str = Field(unique=True)
    glucose_mg_dl: int = Field(ge=0)
    reading_timestamp: str
