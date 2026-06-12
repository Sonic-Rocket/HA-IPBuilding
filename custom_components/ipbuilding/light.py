"""Light platform for the IPBuilding integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, HUB_BY_TYPE, KIND_LIGHT, TYPE_DIMMER, TYPE_RELAY
from .entity import IPBuildingEntity
from .type_aliases import IPBuildingConfigEntry  # noqa: F401

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IPBuildingConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up IPBuilding light entities from a config entry."""
    coordinator = entry.runtime_data.coordinator
    entities: list[LightEntity] = []

    if coordinator.data:
        for device in coordinator.data.values():
            dtype = int(device.get("Type") or 0)
            if dtype == TYPE_DIMMER:
                entities.append(IPBuildingBrightnessLight(coordinator, device))
            elif dtype == TYPE_RELAY and device.get("Kind") == KIND_LIGHT:
                entities.append(IPBuildingOnOffLight(coordinator, device))

    async_add_entities(entities)


class IPBuildingBrightnessLight(IPBuildingEntity, LightEntity):
    """A dimmer that supports brightness 0..255."""

    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(self, coordinator, device: dict[str, Any]) -> None:
        super().__init__(coordinator, device, HUB_BY_TYPE[TYPE_DIMMER][0])
        self._attr_unique_id = f"{coordinator.unique_id_prefix}_dimmer_{self._device_id}"
        self._attr_device_info["model"] = "Dimmer"

    @property
    def is_on(self) -> bool:
        """Return true if the light is on."""
        val = self._read_value()
        if isinstance(val, bool):
            return val
        return int(val or 0) > 0

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        val = self._read_value()
        if isinstance(val, bool):
            return 255 if val else 0
        # IPBuilding dimmer values are 0..100.
        return int(int(val or 0) * 255 / 100)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the dimmer on at the requested brightness."""
        brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
        value = int(brightness * 100 / 255)
        if value == 0 and brightness > 0:
            value = 1
        await self.coordinator.api.set_value(self._device_id, value, "DIM")
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the dimmer off."""
        await self.coordinator.api.set_value(self._device_id, 0, "OFF")
        await self.coordinator.async_request_refresh()

    def _read_value(self) -> Any:
        return (
            self._device_data.get("Status")
            or self._device_data.get("status")
            or self._device_data.get("Value")
            or self._device_data.get("value")
        )


class IPBuildingOnOffLight(IPBuildingEntity, LightEntity):
    """A relay exposed as an on/off light (Kind 1)."""

    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(self, coordinator, device: dict[str, Any]) -> None:
        super().__init__(coordinator, device, HUB_BY_TYPE[TYPE_RELAY][0])
        self._attr_unique_id = f"{coordinator.unique_id_prefix}_relay_light_{self._device_id}"
        self._attr_device_info["model"] = "Relay"

    @property
    def is_on(self) -> bool:
        val = (
            self._device_data.get("Status")
            or self._device_data.get("status")
            or self._device_data.get("Value")
            or self._device_data.get("value")
        )
        if isinstance(val, bool):
            return val
        return int(val or 0) > 0

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.api.set_value(self._device_id, 1, "ON")
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api.set_value(self._device_id, 0, "OFF")
        await self.coordinator.async_request_refresh()
