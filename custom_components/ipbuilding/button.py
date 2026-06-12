"""Button platform for the IPBuilding integration."""
from __future__ import annotations

import logging

from aiohttp import ClientError
from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import HUB_BY_TYPE, TYPE_BUTTON
from .entity import IPBuildingEntity
from .type_aliases import IPBuildingConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IPBuildingConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up IPBuilding button entities from a config entry."""
    coordinator = entry.runtime_data.coordinator
    entities: list[ButtonEntity] = []

    if coordinator.data:
        for device in coordinator.data.values():
            if int(device.get("Type") or 0) == TYPE_BUTTON:
                entities.append(IPBuildingButton(coordinator, device))

    async_add_entities(entities)


class IPBuildingButton(IPBuildingEntity, ButtonEntity):
    """Representation of an IPBuilding button."""

    _attr_entity_registry_enabled_default = False
    _attr_entity_registry_visible_default = False

    def __init__(self, coordinator, device: dict) -> None:
        super().__init__(coordinator, device, HUB_BY_TYPE[TYPE_BUTTON][0])
        self._attr_unique_id = f"{coordinator.unique_id_prefix}_button_{self._device_id}"
        self._attr_device_info["model"] = "Button"

    async def async_press(self) -> None:
        """Handle the button press by sending a 1/ON to the controller."""
        try:
            await self.coordinator.api.set_value(self._device_id, 1, "ON")
        except ClientError as err:
            _LOGGER.warning(
                "Failed to press IPBuilding button %s: %s", self._device_id, err
            )
