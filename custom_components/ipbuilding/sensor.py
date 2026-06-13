"""Sensor platform for the IPBuilding integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import HUB_BY_TYPE, TYPE_DIMMER, TYPE_RELAY, TYPE_REGIME, TYPE_TIME
from .entity import IPBuildingEntity
from .type_aliases import IPBuildingConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IPBuildingConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up IPBuilding sensor entities from a config entry."""
    coordinator = entry.runtime_data.coordinator
    entities: list[SensorEntity] = []

    if coordinator.data:
        for device in coordinator.data.values():
            dtype = int(device.get("Type") or 0)
            if dtype == TYPE_TIME:
                entities.append(
                    IPBuildingSystemSensor(
                        coordinator, device, "Time", HUB_BY_TYPE[TYPE_TIME][0]
                    )
                )
            elif dtype == TYPE_REGIME:
                entities.append(
                    IPBuildingSystemSensor(
                        coordinator, device, "Regime", HUB_BY_TYPE[TYPE_REGIME][0]
                    )
                )
            elif dtype in (TYPE_RELAY, TYPE_DIMMER) and "Watt" in device:
                entities.append(IPBuildingPowerSensor(coordinator, device))

    async_add_entities(entities)


def _to_int(value: Any) -> int:
    """Convert a possibly-None / bool / str value to int, defaulting to 0."""
    if value is None:
        return 0
    if isinstance(value, bool):
        return 1 if value else 0
    return int(value)


class IPBuildingSystemSensor(IPBuildingEntity, SensorEntity):
    """Generic sensor for Time and Regime devices."""

    def __init__(
        self,
        coordinator,
        device: dict,
        sensor_type: str,
        hub: str,
    ) -> None:
        super().__init__(coordinator, device, hub)
        self._attr_unique_id = f"ipbuilding_sensor_{self._device_id}"
        # Inherit the entity name from the device (set in the base
        # ``IPBuildingEntity.__init__`` as ``DeviceInfo.name``).
        self._attr_device_info["model"] = sensor_type
        self._attr_entity_registry_visible_default = False

    @property
    def native_value(self) -> Any:
        """Return the raw value reported by the controller."""
        d = self._device_data
        return d.get("Value") or d.get("value")


class IPBuildingPowerSensor(IPBuildingEntity, SensorEntity):
    """A power sensor derived from a relay/dimmer's Watt attribute and state.

    The reported wattage is an **estimate**: for dimmers it scales
    ``Watt`` by the dimmer's percentage, and for relays it reports
    ``Watt`` when on and ``0`` when off. ``SensorStateClass.MEASUREMENT``
    is set so that downstream ``integration`` helper sensors can convert
    the value to kWh for Home Assistant's Energy Dashboard. The sensor
    is hidden by default; if you do not use the integration helper, you
    can leave the entity disabled. The estimate is good enough for
    at-a-glance energy dashboards but should not be used for billing.
    """

    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_visible_default = False

    def __init__(self, coordinator, device: dict) -> None:
        dtype = int(device.get("Type") or 0)
        hub_id, _ = HUB_BY_TYPE[dtype]
        super().__init__(coordinator, device, hub_id)
        self._attr_unique_id = f"ipbuilding_power_{self._device_id}"
        # Distinguish the power sensor from the parent device in the UI
        # ("Kitchen Dimmer" / "Kitchen Dimmer Power") while keeping the
        # entity_id short ("sensor.kitchen_dimmer_power"). The base class
        # leaves ``_attr_name`` as ``None`` so we set only the suffix here.
        self._attr_name = "Power"
        self._attr_device_info["model"] = "Dimmer" if dtype == TYPE_DIMMER else "Relay"

    @property
    def native_value(self) -> float:
        """Return the estimated power usage in Watts."""
        d = self._device_data
        rated_watt = float(d.get("Watt") or 0)

        raw = (
            d.get("Status")
            or d.get("status")
            or d.get("Value")
            or d.get("value")
        )
        value = _to_int(raw)
        type_id = int(d.get("Type") or d.get("type") or 0)

        if type_id == TYPE_DIMMER:
            # Dimmer value is 0..100.
            return round(rated_watt * (value / 100.0), 1)
        return rated_watt if value > 0 else 0
