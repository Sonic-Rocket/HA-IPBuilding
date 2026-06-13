"""Tests for the IPBuilding light platform."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ipbuilding.const import CONF_HOST, CONF_PORT, DOMAIN


async def test_brightness_mapping(
    hass: HomeAssistant, mock_setup_entry, ipbuilding_devices
) -> None:
    """Dimmer brightness should be exposed as 0..255 even though the API uses 0..100."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.0.2.10", CONF_PORT: 30200},
        entry_id="test-light",
        unique_id="192.0.2.10:30200",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.ipbuilding.IPBuildingAPI") as mock_api_cls:
        mock_api = mock_api_cls.return_value
        mock_api.get_devices = AsyncMock(return_value=ipbuilding_devices)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    # Drive the dimmer to 40% via the API and let the coordinator refresh.
    ipbuilding_devices[0]["Status"] = 40
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    # Recreate the patched api to allow reload to install its own.
    with patch("custom_components.ipbuilding.IPBuildingAPI") as mock_api_cls:
        mock_api = mock_api_cls.return_value
        mock_api.get_devices = AsyncMock(return_value=ipbuilding_devices)
        await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("light.kitchen_dimmer")
    assert state is not None
    # 40 of 100 == 102 of 255
    assert int(state.attributes.get("brightness", -1)) == 102


async def test_turn_on_calls_api(
    hass: HomeAssistant, mock_setup_entry, ipbuilding_devices
) -> None:
    """Calling turn_on on a dimmer should hit the API with a DIM action."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.0.2.10", CONF_PORT: 30200},
        entry_id="test-light-2",
        unique_id="192.0.2.10:30200",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.ipbuilding.IPBuildingAPI") as mock_api_cls:
        mock_api = mock_api_cls.return_value
        mock_api.get_devices = AsyncMock(return_value=ipbuilding_devices)
        mock_api.set_value = AsyncMock(return_value=None)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": "light.kitchen_dimmer", "brightness": 128},
        blocking=True,
    )

    mock_api.set_value.assert_awaited()
    args, kwargs = mock_api.set_value.call_args
    # 128/255 * 100 = 50
    assert args[0] == 1
    assert args[1] == 50
    assert args[2] == "DIM"


async def test_entity_unique_id_format(
    hass: HomeAssistant, mock_setup_entry, ipbuilding_devices
) -> None:
    """Entity unique_ids must not include the entry_id.

    Including the entry_id in the unique_id makes every entity appear as
    "new" on every reinstall, doubling the entities in Home Assistant.
    The format is pinned here so the regression does not return.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.0.2.10", CONF_PORT: 30200},
        entry_id="test-unique-id",
        unique_id="192.0.2.10:30200",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.ipbuilding.IPBuildingAPI") as mock_api_cls:
        mock_api = mock_api_cls.return_value
        mock_api.get_devices = AsyncMock(return_value=ipbuilding_devices)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    registry = er.async_get(hass)
    for entity in registry.entities.values():
        if entity.platform != DOMAIN:
            continue
        # No entry_id or "ipbuilding_{entry_id}_" prefix allowed.
        assert entry.entry_id not in entity.unique_id, (
            f"Entity {entity.entity_id} unique_id {entity.unique_id!r} must not "
            f"contain the entry_id; that breaks upgrades."
        )
        assert entity.unique_id.startswith("ipbuilding_"), (
            f"Entity {entity.entity_id} unique_id {entity.unique_id!r} must "
            f"start with 'ipbuilding_'."
        )
