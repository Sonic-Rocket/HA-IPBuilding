"""Scene platform for the IPBuilding integration."""
from __future__ import annotations

import logging

from aiohttp import ClientError
from homeassistant.components.scene import Scene
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import HUB_BY_TYPE, TYPE_SPHERE, TYPE_TEMP_SPHERE
from .entity import IPBuildingEntity
from .type_aliases import IPBuildingConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IPBuildingConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up IPBuilding scene entities from a config entry."""
    coordinator = entry.runtime_data.coordinator
    entities: list[Scene] = []

    if coordinator.data:
        for device in coordinator.data.values():
            dtype = int(device.get("Type") or 0)
            if dtype in (TYPE_SPHERE, TYPE_TEMP_SPHERE):
                entities.append(IPBuildingScene(coordinator, device))

    async_add_entities(entities)


class IPBuildingScene(IPBuildingEntity, Scene):
    """Representation of an IPBuilding sphere (scene)."""

    def __init__(self, coordinator, device: dict) -> None:
        dtype = int(device.get("Type") or 0)
        hub_id, _ = HUB_BY_TYPE[dtype]
        super().__init__(coordinator, device, hub_id)
        self._attr_unique_id = f"{coordinator.unique_id_prefix}_scene_{self._device_id}"
        self._attr_device_info["model"] = "Scene"

    async def async_activate(self, **kwargs) -> None:
        """Activate the scene by sending a 1/ON to the controller."""
        try:
            await self.coordinator.api.set_value(self._device_id, 1, "ON")
        except ClientError as err:
            _LOGGER.warning(
                "Failed to activate IPBuilding scene %s: %s", self._device_id, err
            )
