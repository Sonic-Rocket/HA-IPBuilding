"""DataUpdateCoordinator for the IPBuilding integration."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import IPBuildingAPI, IPBuildingAPIError
from .const import DOMAIN, POLLED_DEVICE_TYPES

_LOGGER = logging.getLogger(__name__)


class IPBuildingDataCoordinator(DataUpdateCoordinator[dict[Any, dict[str, Any]]]):
    """Coordinator that polls the IPBuilding controller for state updates."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: IPBuildingAPI,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(seconds=20),
        )
        self.api = api
        self._initial_data: dict[Any, dict[str, Any]] = {}

    @property
    def unique_id_prefix(self) -> str:
        """Return a prefix used to build entity unique_ids for this entry."""
        return f"ipbuilding_{self.config_entry.entry_id}"

    async def _async_setup(self) -> None:
        """Perform a one-time full fetch of every device on the controller."""
        devices = await self.api.get_devices()
        self._initial_data = {
            d.get("ID") or d.get("id"): d for d in devices if d.get("ID") or d.get("id")
        }

    async def _async_update_data(self) -> dict[Any, dict[str, Any]]:
        """Fetch the latest values for the polled device types.

        Returns a NEW dict that merges the initial full snapshot with the
        partial refresh of polled types. Always returns a fresh dict to
        avoid in-place mutation of coordinator state by entity optimistic
        updates.
        """
        try:
            partial = await self.api.get_devices(list(POLLED_DEVICE_TYPES))
        except IPBuildingAPIError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        new_data: dict[Any, dict[str, Any]] = dict(self._initial_data)
        for d in partial:
            key = d.get("ID") or d.get("id")
            if key is not None:
                new_data[key] = d
        return new_data
