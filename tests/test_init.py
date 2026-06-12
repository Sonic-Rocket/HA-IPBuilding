"""Tests for the IPBuilding __init__ module."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ipbuilding.api import IPBuildingCannotConnect
from custom_components.ipbuilding.const import CONF_HOST, CONF_PORT, DOMAIN


async def test_setup_entry_success(
    hass: HomeAssistant, mock_setup_entry, ipbuilding_devices
) -> None:
    """A successful connection should load the entry and create hub devices."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.0.2.10", CONF_PORT: 30200},
        entry_id="test-entry-1",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.ipbuilding.IPBuildingAPI"
    ) as mock_api_cls:
        mock_api = mock_api_cls.return_value
        mock_api.get_devices = AsyncMock(return_value=ipbuilding_devices)

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data is not None
    assert entry.runtime_data.api is mock_api

    # Hub devices for present types should be registered.
    dev_reg = dr.async_get(hass)
    hubs = [
        d
        for d in dev_reg.devices.values()
        if any(ident[0] == DOMAIN and ident[1].startswith("hub_") for ident in d.identifiers)
    ]
    assert any(h.name == "IPBuilding Dimmers" for h in hubs)
    assert any(h.name == "IPBuilding Relays" for h in hubs)


async def test_setup_entry_cannot_connect(
    hass: HomeAssistant, mock_setup_entry
) -> None:
    """If the controller is unreachable the entry should retry via NotReady."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.0.2.99", CONF_PORT: 30200},
        entry_id="test-entry-2",
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.ipbuilding.IPBuildingAPI"
    ) as mock_api_cls:
        mock_api = mock_api_cls.return_value
        mock_api.get_devices = AsyncMock(
            side_effect=IPBuildingCannotConnect("nope")
        )

        with pytest.raises(ConfigEntryNotReady):
            await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.SETUP_RETRY
