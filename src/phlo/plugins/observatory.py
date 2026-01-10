"""Observatory extension manifest models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ObservatoryExtensionCompatibility(BaseModel):
    """Compatibility requirements for an Observatory extension."""

    observatory_min: str = Field(..., description="Minimum supported Observatory version")


class ObservatoryExtensionSettings(BaseModel):
    """Settings schema and defaults for an extension."""

    schema: dict[str, Any]
    defaults: dict[str, Any] = Field(default_factory=dict)
    scope: Literal["global", "extension"] = "extension"


class ObservatoryExtensionRoute(BaseModel):
    """Route registration entry for an extension."""

    path: str
    module: str
    export: str = "registerRoutes"


class ObservatoryExtensionNavItem(BaseModel):
    """Navigation entry for an extension."""

    title: str
    to: str


class ObservatoryExtensionSlot(BaseModel):
    """Slot registration entry for an extension."""

    slot_id: str
    module: str
    export: str = "registerSlot"


class ObservatoryExtensionSettingsPanel(BaseModel):
    """Settings panel registration entry for an extension."""

    module: str
    export: str = "registerSettings"


class ObservatoryExtensionUI(BaseModel):
    """UI contributions for an extension."""

    routes: list[ObservatoryExtensionRoute] = Field(default_factory=list)
    nav: list[ObservatoryExtensionNavItem] = Field(default_factory=list)
    slots: list[ObservatoryExtensionSlot] = Field(default_factory=list)
    settings: list[ObservatoryExtensionSettingsPanel] = Field(default_factory=list)


class ObservatoryExtensionManifest(BaseModel):
    """Manifest contract for Observatory extensions."""

    name: str
    version: str
    compat: ObservatoryExtensionCompatibility
    settings: ObservatoryExtensionSettings | None = None
    ui: ObservatoryExtensionUI = Field(default_factory=ObservatoryExtensionUI)
