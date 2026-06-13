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
    """Coordinator that polls the IPBuilding controller for state updates.

    Polling is conditional: if the initial full snapshot does not contain any
    device of a polled type (RELAY, DIMMER, DMX, LED), the update interval is
    set to ``None`` and the controller is only refreshed when an entity
    triggers ``async_request_refresh`` (e.g. after a button press or scene
    activation). This avoids wasting a request every 20 s for users who only
    have buttons, sensors or scenes.
    """

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
        # Tracks how many consecutive partial polls missed a previously-seen
        # polled-type device id. Used by ``_async_update_data`` to detect
        # devices that disappeared from the controller.
        self._missing_since: dict[Any, int] = {}

    async def _async_setup(self) -> None:
        """Perform a one-time full fetch of every device on the controller."""
        devices = await self.api.get_devices()
        self._initial_data = {
            d.get("ID") or d.get("id"): d for d in devices if d.get("ID") or d.get("id")
        }
        # If no polled-type device is present, stop polling automatically.
        present_types = {
            int(d.get("Type") or d.get("type") or 0) for d in self._initial_data.values()
        }
        if not (present_types & set(POLLED_DEVICE_TYPES)):
            self.update_interval = None
            _LOGGER.debug(
                "No polled-type devices present; coordinator polling disabled, "
                "will only refresh on explicit async_request_refresh"
            )

    async def _async_update_data(self) -> dict[Any, dict[str, Any]]:
        """Fetch the latest values for the polled device types.

        Returns a NEW dict that merges the initial full snapshot with the
        partial refresh of polled types. Always returns a fresh dict to
        avoid in-place mutation of coordinator state by entity optimistic
        updates.

        Removal: devices that were present in the previous partial poll but
        are absent from the current one are tracked in ``_missing_since``.
        They are only dropped from the coordinator data after two
        consecutive missed polls, which guards against transient network
        blips while still letting entities eventually disappear when the
        device is removed on the controller.
        """
        try:
            partial = await self.api.get_devices(list(POLLED_DEVICE_TYPES))
        except IPBuildingAPIError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        partial_ids: set[Any] = set()
        new_data: dict[Any, dict[str, Any]] = dict(self._initial_data)
        for d in partial:
            key = d.get("ID") or d.get("id")
            if key is None:
                continue
            partial_ids.add(key)
            new_data[key] = d
            # If the device is back, clear any previous miss count.
            self._missing_since.pop(key, None)

        # Update removal tracking for any *polled-type* device that was
        # present in the initial snapshot or in a previous partial poll
        # but is missing from the current partial. The miss counter is
        # incremented each consecutive miss; the device is only dropped
        # from the coordinator snapshot after the second consecutive
        # miss, which guards against transient network blips while
        # still letting entities eventually disappear when the device
        # is removed on the controller.
        #
        # Non-polled types (buttons, sensors, scenes, time/regime
        # sensors) are intentionally excluded: the partial poll only
        # asks for ``POLLED_DEVICE_TYPES``, so any non-polled device
        # would be marked missing on every poll and silently dropped
        # after 40 s. The initial full snapshot is the source of
        # truth for those devices and is never re-validated here.
        polled_seen = {
            key
            for key, dev in self._initial_data.items()
            if int(dev.get("Type") or dev.get("type") or 0) in POLLED_DEVICE_TYPES
        } | set(self._missing_since)
        for key in polled_seen - partial_ids:
            self._missing_since[key] = self._missing_since.get(key, 0) + 1
            if self._missing_since[key] >= 2:
                new_data.pop(key, None)
                self._missing_since.pop(key, None)
                _LOGGER.debug(
                    "Device %s missing for 2 consecutive polls; removing from "
                    "coordinator snapshot",
                    key,
                )

        return new_data
