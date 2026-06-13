"""Tests for the IPBuilding data coordinator."""
from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ipbuilding.api import IPBuildingAPIError
from custom_components.ipbuilding.const import (
    CONF_HOST,
    CONF_PORT,
    DOMAIN,
    POLLED_DEVICE_TYPES,
)
from custom_components.ipbuilding.coordinator import IPBuildingDataCoordinator


def _make_api(get_devices_return: list[dict] | Exception) -> IPBuildingDataCoordinator:
    """Build a coordinator wired to a MagicMock API with the given return."""
    api = MagicMock()
    if isinstance(get_devices_return, Exception):
        api.get_devices = AsyncMock(side_effect=get_devices_return)
    else:
        api.get_devices = AsyncMock(return_value=get_devices_return)
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.0.2.10", CONF_PORT: 30200},
    )
    hass = MagicMock(spec=HomeAssistant)
    coord = IPBuildingDataCoordinator(hass, entry, api)  # type: ignore[arg-type]
    return coord


async def test_initial_setup_populates_snapshot() -> None:
    """_async_setup should populate _initial_data from the first full fetch."""
    coord = _make_api(
        [
            {"ID": 1, "Type": 2},
            {"ID": 2, "Type": 1},
        ]
    )
    await coord._async_setup()
    assert {k for k in coord._initial_data} == {1, 2}


async def test_polling_disabled_when_no_polled_types_present() -> None:
    """If no POLLED_DEVICE_TYPES device is present, interval is set to None."""
    # Sensors/buttons/scenes only — nothing the coordinator polls.
    coord = _make_api(
        [
            {"ID": 50, "Type": 50},  # button
            {"ID": 100, "Type": 100},  # sphere
        ]
    )
    assert coord.update_interval == timedelta(seconds=20)
    await coord._async_setup()
    assert coord.update_interval is None


async def test_polling_kept_when_polled_types_present() -> None:
    """If at least one polled-type device is present, the 20s interval sticks."""
    coord = _make_api([{"ID": 1, "Type": 1}])  # relay
    await coord._async_setup()
    assert coord.update_interval == timedelta(seconds=20)


async def test_update_merges_partial_over_initial() -> None:
    """The partial poll should overwrite matching keys in the initial snapshot."""
    coord = _make_api([{"ID": 1, "Type": 1, "Status": 0}])
    await coord._async_setup()

    # The coordinator uses the same MagicMock for both calls; reset it and
    # queue the partial response.
    coord.api.get_devices = AsyncMock(  # type: ignore[attr-defined]
        return_value=[{"ID": 1, "Type": 1, "Status": 1}]
    )
    new_data = await coord._async_update_data()
    assert new_data[1]["Status"] == 1


async def test_update_raises_update_failed_on_api_error() -> None:
    """An IPBuildingAPIError during update should surface as UpdateFailed."""
    coord = _make_api(IPBuildingAPIError("boom"))
    with pytest.raises(UpdateFailed):
        await coord._async_update_data()


async def test_device_removed_after_two_missed_polls() -> None:
    """A device that disappears from the partial for 2 polls should be dropped."""
    coord = _make_api(
        [
            {"ID": 1, "Type": 1, "Status": 0},
            {"ID": 2, "Type": 1, "Status": 0},
        ]
    )
    await coord._async_setup()

    # First poll: ID 2 disappears.
    coord.api.get_devices = AsyncMock(  # type: ignore[attr-defined]
        return_value=[{"ID": 1, "Type": 1, "Status": 1}]
    )
    data = await coord._async_update_data()
    assert 2 in data  # still present after the first miss.

    # Second poll: ID 2 still missing -> removed.
    data = await coord._async_update_data()
    assert 2 not in data


async def test_device_return_clears_miss_counter() -> None:
    """A device that reappears in a partial should not be removed later."""
    coord = _make_api([{"ID": 1, "Type": 1}, {"ID": 2, "Type": 1}])
    await coord._async_setup()

    # First poll: ID 2 missing.
    coord.api.get_devices = AsyncMock(  # type: ignore[attr-defined]
        return_value=[{"ID": 1, "Type": 1}]
    )
    await coord._async_update_data()

    # Second poll: ID 2 back. Counter should reset, device stays in data.
    coord.api.get_devices = AsyncMock(  # type: ignore[attr-defined]
        return_value=[{"ID": 1, "Type": 1}, {"ID": 2, "Type": 1}]
    )
    data = await coord._async_update_data()
    assert 2 in data
    assert 2 not in coord._missing_since  # type: ignore[attr-defined]


async def test_non_polled_device_not_removed_on_partial_miss() -> None:
    """Non-polled devices (buttons, sensors, scenes) must never be removed by
    the partial-poll removal logic.

    Regression test for the rc2 bug where ``_initial_data`` was used
    directly as the removal-tracking seed set, which meant a button or
    sensor that was present at setup but never returned by the partial
    poll (because the partial only asks for ``POLLED_DEVICE_TYPES``)
    would be marked missing on every poll and dropped from the
    coordinator snapshot after 40 s.
    """
    coord = _make_api(
        [
            {"ID": 1, "Type": 1, "Status": 0},  # relay (polled)
            {"ID": 50, "Type": 50, "Status": 0},  # button (not polled)
            {"ID": 100, "Type": 100, "Status": 0},  # sphere (not polled)
            {"ID": 200, "Type": 56, "Value": 1},  # time sensor (not polled)
        ]
    )
    await coord._async_setup()

    # Partial poll returns only the relay — buttons, spheres and
    # sensors are filtered out by the controller because we asked for
    # POLLED_DEVICE_TYPES only.
    coord.api.get_devices = AsyncMock(  # type: ignore[attr-defined]
        return_value=[{"ID": 1, "Type": 1, "Status": 1}]
    )

    # Run many polls; non-polled devices must survive every one.
    for _ in range(5):
        data = await coord._async_update_data()

    # All four devices are still in the coordinator snapshot.
    assert 1 in data
    assert 50 in data  # button
    assert 100 in data  # sphere
    assert 200 in data  # time sensor

    # The miss counter only tracked the polled device, not the others.
    assert 1 not in coord._missing_since  # type: ignore[attr-defined]
    assert 50 not in coord._missing_since
    assert 100 not in coord._missing_since
    assert 200 not in coord._missing_since


async def test_polled_device_removed_only_after_two_misses_in_mixed_setup() -> None:
    """In a mixed setup, a polled device that disappears should still be
    removed after two missed partial polls; non-polled devices are not
    affected by the removal cycle at all.
    """
    coord = _make_api(
        [
            {"ID": 1, "Type": 1, "Status": 0},  # relay (polled)
            {"ID": 2, "Type": 1, "Status": 0},  # relay (polled) — will be removed
            {"ID": 50, "Type": 50, "Status": 0},  # button (not polled)
        ]
    )
    await coord._async_setup()

    # First miss: ID 2 gone. Relay is still in the snapshot.
    coord.api.get_devices = AsyncMock(  # type: ignore[attr-defined]
        return_value=[{"ID": 1, "Type": 1, "Status": 1}]
    )
    data = await coord._async_update_data()
    assert 1 in data
    assert 2 in data  # one miss is not enough
    assert 50 in data

    # Second consecutive miss: ID 2 dropped. Button unaffected.
    data = await coord._async_update_data()
    assert 1 in data
    assert 2 not in data
    assert 50 in data  # button still here, never tracked for removal


async def test_polled_device_types_set_is_non_empty() -> None:
    """Sanity: the polled set should be non-empty and contain the relay/dimmer types."""
    assert POLLED_DEVICE_TYPES
    assert 1 in POLLED_DEVICE_TYPES  # TYPE_RELAY
    assert 2 in POLLED_DEVICE_TYPES  # TYPE_DIMMER
