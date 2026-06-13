"""Switch platform for the IPBuilding integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    HUB_BY_TYPE,
    KIND_AUTOMATION,
    KIND_FAN,
    KIND_LOCK,
    KIND_SOCKET,
    KIND_VALVE,
    TYPE_RELAY,
)
from .entity import IPBuildingEntity
from .type_aliases import IPBuildingConfigEntry

_LOGGER = logging.getLogger(__name__)


# Kind -> (device class, icon) for relays that act as switches.
_KIND_DEVICE_CLASS: dict[int, tuple[SwitchDeviceClass | None, str | None]] = {
    KIND_SOCKET: (SwitchDeviceClass.OUTLET, "mdi:power-socket-eu"),
    KIND_LOCK: (SwitchDeviceClass.SWITCH, "mdi:lock"),
    KIND_FAN: (SwitchDeviceClass.SWITCH, "mdi:fan"),
    KIND_VALVE: (SwitchDeviceClass.SWITCH, "mdi:valve"),
    KIND_AUTOMATION: (SwitchDeviceClass.SWITCH, "mdi:robot"),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IPBuildingConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up IPBuilding switch entities from a config entry."""
    coordinator = entry.runtime_data.coordinator
    entities: list[SwitchEntity] = []

    if coordinator.data:
        for device in coordinator.data.values():
            if int(device.get("Type") or 0) != TYPE_RELAY:
                continue
            # Skip relays that the light platform already exposed.
            if device.get("Kind") == 1:
                continue
            entities.append(IPBuildingSwitch(coordinator, device))

    async_add_entities(entities)


class IPBuildingSwitch(IPBuildingEntity, SwitchEntity):
    """Representation of an IPBuilding relay that is not a light."""

    def __init__(self, coordinator, device: dict[str, Any]) -> None:
        super().__init__(coordinator, device, HUB_BY_TYPE[TYPE_RELAY][0])
        self._attr_unique_id = f"ipbuilding_relay_{self._device_id}"
        self._attr_device_info["model"] = "Relay"

        kind = device.get("Kind")
        if (mapping := _KIND_DEVICE_CLASS.get(kind)) is not None:
            device_class, icon = mapping
            if device_class is not None:
                self._attr_device_class = device_class
            if icon is not None:
                self._attr_icon = icon

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
