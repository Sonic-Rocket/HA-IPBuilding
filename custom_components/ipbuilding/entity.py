"""Base entity for the IPBuilding integration."""
from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import IPBuildingDataCoordinator


class IPBuildingEntity(CoordinatorEntity[IPBuildingDataCoordinator]):
    """Base entity for IPBuilding devices.

    Provides common device-info, available and _device_data plumbing so that
    platform implementations only have to override domain-specific behaviour.
    """

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: IPBuildingDataCoordinator,
        device: dict[str, Any],
        hub_id: str,
    ) -> None:
        """Initialize the base entity."""
        super().__init__(coordinator)
        self._device_id = device.get("ID") or device.get("id")
        self._initial_device_data = device
        self._attr_unique_id = f"{coordinator.unique_id_prefix}_{self._device_id}"
        self._attr_name = (
            device.get("Description")
            or device.get("name")
            or f"Device {self._device_id}"
        )

        info: dict[str, Any] = {
            "identifiers": {(DOMAIN, f"output_{self._device_id}")},
            "name": self._attr_name,
            "manufacturer": MANUFACTURER,
            "via_device": (DOMAIN, hub_id),
        }
        if group := device.get("Group"):
            info["suggested_area"] = group.get("Name")
        self._attr_device_info = DeviceInfo(**info)

    @property
    def _device_data(self) -> dict[str, Any]:
        """Return the latest device data from the coordinator."""
        if self.coordinator.data is None:
            return self._initial_device_data
        return self.coordinator.data.get(
            self._device_id, self._initial_device_data
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self._device_data.get(
            "Visible", True
        )
