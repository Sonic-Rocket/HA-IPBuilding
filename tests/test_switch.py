"""Tests for the IPBuilding switch platform."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ipbuilding.const import (
    CONF_HOST,
    CONF_PORT,
    DOMAIN,
    KIND_AUTOMATION,
    KIND_FAN,
    KIND_LOCK,
    KIND_SOCKET,
    KIND_VALVE,
)


async def test_switch_relay_creates_entity(
    hass: HomeAssistant, mock_setup_entry, ipbuilding_devices
) -> None:
    """A relay (Type=1) with a non-light Kind should become a switch entity."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.0.2.10", CONF_PORT: 30200},
        entry_id="test-switch",
        unique_id="192.0.2.10:30200",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.ipbuilding.IPBuildingAPI") as mock_api_cls:
        mock_api = mock_api_cls.return_value
        mock_api.get_devices = AsyncMock(return_value=ipbuilding_devices)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    # ipbuilding_devices contains 1 dimmer, 1 light relay, 1 socket relay.
    # Only the socket relay (Kind=2) should show up as a switch. The light
    # relay (Kind=1) becomes a light entity but shares the same underlying
    # unique_id prefix (ipbuilding_relay_), so we filter on entity_id
    # domain rather than the unique_id prefix.
    registry = er.async_get(hass)
    switch_entities = [
        e for e in registry.entities.values()
        if e.platform == DOMAIN and e.entity_id.startswith("switch.")
    ]
    assert len(switch_entities) == 1
    assert switch_entities[0].unique_id == "ipbuilding_relay_3"


async def test_switch_kind_device_class_mapping(
    hass: HomeAssistant, mock_setup_entry
) -> None:
    """Each Kind value should map to the right SwitchDeviceClass and icon."""
    devices = [
        {"ID": 100, "Type": 1, "Kind": KIND_SOCKET, "Description": "S", "Status": 0, "Visible": True},
        {"ID": 101, "Type": 1, "Kind": KIND_LOCK, "Description": "L", "Status": 0, "Visible": True},
        {"ID": 102, "Type": 1, "Kind": KIND_FAN, "Description": "F", "Status": 0, "Visible": True},
        {"ID": 103, "Type": 1, "Kind": KIND_VALVE, "Description": "V", "Status": 0, "Visible": True},
        {"ID": 104, "Type": 1, "Kind": KIND_AUTOMATION, "Description": "A", "Status": 0, "Visible": True},
    ]
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.0.2.10", CONF_PORT: 30200},
        entry_id="test-switch-kinds",
        unique_id="192.0.2.10:30200",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.ipbuilding.IPBuildingAPI") as mock_api_cls:
        mock_api = mock_api_cls.return_value
        mock_api.get_devices = AsyncMock(return_value=devices)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("switch.s")
    assert state is not None
    assert state.attributes.get("device_class") == "outlet"
    assert state.attributes.get("icon") == "mdi:power-socket-eu"

    icon_expectations = [
        ("switch.l", "mdi:lock"),
        ("switch.f", "mdi:fan"),
        ("switch.v", "mdi:valve"),
        ("switch.a", "mdi:robot"),
    ]
    for eid, expected_icon in icon_expectations:
        s = hass.states.get(eid)
        assert s is not None, f"Missing switch entity {eid}"
        assert s.attributes.get("icon") == expected_icon


async def test_switch_turn_on_calls_api(
    hass: HomeAssistant, mock_setup_entry, ipbuilding_devices
) -> None:
    """Calling turn_on on a switch should hit the API with ON action."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.0.2.10", CONF_PORT: 30200},
        entry_id="test-switch-on",
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
        "switch",
        "turn_on",
        {"entity_id": "switch.coffee_socket"},
        blocking=True,
    )

    mock_api.set_value.assert_awaited()
    args, _kwargs = mock_api.set_value.call_args
    assert args[0] == 3
    assert args[1] == 1
    assert args[2] == "ON"
