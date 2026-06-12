"""Type aliases shared across the IPBuilding integration.

Centralises the typed ``ConfigEntry`` alias so platform modules can import
it from a stable location without depending on ``__init__`` directly.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry

if TYPE_CHECKING:
    from .api import IPBuildingAPI
    from .coordinator import IPBuildingDataCoordinator


@dataclass
class IPBuildingData:
    """Runtime data held by the config entry."""

    api: "IPBuildingAPI"
    coordinator: "IPBuildingDataCoordinator"


#: Typed config entry used by every platform in the integration.
type IPBuildingConfigEntry = ConfigEntry[IPBuildingData]

__all__ = ["IPBuildingConfigEntry", "IPBuildingData"]
