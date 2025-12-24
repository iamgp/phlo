"""PhloSchema base class with smart defaults.

Provides a base Pandera DataFrameModel with phlo's default configuration,
eliminating the need to specify Config on every schema.
"""

from __future__ import annotations

from pandera.pandas import DataFrameModel


class PhloSchema(DataFrameModel):
    """Base schema with phlo smart defaults.

    Extends Pandera DataFrameModel with standard phlo configuration:
    - strict=False: Allow extra columns (DLT metadata like _dlt_id, _dlt_load_id)
    - coerce=True: Automatically coerce types to match schema

    Note: For optional fields (str | None), you must use Field(nullable=True).
    This is a Pandera requirement when coerce=True.

    Example:
        from phlo_quality.schemas import PhloSchema
        from pandera.pandas import Field

        class RawUserEvents(PhloSchema):
            id: str = Field(unique=True)
            type: str
            actor_login: str | None = Field(nullable=True)  # Required for nullable!
            created_at: str
            # No Config needed - defaults are applied automatically
    """

    class Config:
        strict = False  # Allow extra columns (DLT metadata)
        coerce = True  # Auto-coerce types
