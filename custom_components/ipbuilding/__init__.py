"""The IPBuilding integration."""
from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import IPBuildingAPI, IPBuildingCannotConnect
from .const import DOMAIN, HUB_BY_TYPE
from .coordinator import IPBuildingDataCoordinator
from .type_aliases import IPBuildingConfigEntry

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.LIGHT,
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.SENSOR,
    Platform.SCENE,
]


@dataclass
class IPBuildingData:
    """Runtime data held by the config entry."""

    api: IPBuildingAPI
    coordinator: IPBuildingDataCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: IPBuildingConfigEntry
) -> bool:
    """Set up IPBuilding from a config entry."""
    session = async_get_clientsession(hass)
    api = IPBuildingAPI(
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        session=session,
    )
    coordinator = IPBuildingDataCoordinator(hass, entry, api)

    # Populate the initial full snapshot; this also validates connectivity.
    try:
        await coordinator.async_config_entry_first_refresh()
    except IPBuildingCannotConnect as err:
        raise ConfigEntryNotReady(
            f"Cannot connect to IPBuilding controller: {err}"
        ) from err

    # Make the runtime data available to platforms.
    entry.runtime_data = IPBuildingData(api=api, coordinator=coordinator)

    # Register a "hub" device per device type family that has at least one
    # device present. This keeps the device tree tidy in the UI.
    _register_hubs(hass, entry, coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: IPBuildingConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


def _register_hubs(
    hass: HomeAssistant,
    entry: IPBuildingConfigEntry,
    coordinator: IPBuildingDataCoordinator,
) -> None:
    """Create one hub device per device-type family that has any devices."""
    if coordinator.data is None:
        return

    present_types = {
        int(d.get("Type") or d.get("type") or 0)
        for d in coordinator.data.values()
    }

    dev_reg = dr.async_get(hass)
    seen_hubs: set[str] = set()
    for type_id, (hub_id, hub_name) in HUB_BY_TYPE.items():
        if type_id not in present_types or hub_id in seen_hubs:
            continue
        seen_hubs.add(hub_id)
        dev_reg.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, hub_id)},
            name=hub_name,
            manufacturer="IPBuilding",
            model="System Hub",
        )
