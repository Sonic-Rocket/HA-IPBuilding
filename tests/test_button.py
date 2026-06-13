"""Tests for the IPBuilding button platform."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from aiohttp import ClientError
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ipbuilding.button import IPBuildingButton
from custom_components.ipbuilding.const import CONF_HOST, CONF_PORT, DOMAIN


async def _trigger_button_press(
    hass: HomeAssistant,
    coordinator,
    device: dict,
) -> None:
    """Construct an IPBuildingButton in isolation and call ``async_press``.

    The button entity is registered with
    ``_attr_entity_registry_enabled_default = False`` to keep it off the
    dashboard, which means the platform helper short-circuits it before
    it ever lands in the entity component's ``_entities`` dict. Service
    calls into ``button.press`` therefore bounce off
    "Referenced entities X are missing or not currently available" in
    the test environment. To exercise the actual ``async_press``
    implementation we instantiate the class directly with a stub
    coordinator and drive it ourselves.
    """
    button = IPBuildingButton(coordinator, device)
    button.hass = hass
    await button.async_press()


async def test_button_press_calls_api(
    hass: HomeAssistant, mock_setup_entry, ipbuilding_button_device
) -> None:
    """Pressing a button should send value=1, actionType=ON to the controller."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.0.2.10", CONF_PORT: 30200},
        entry_id="test-button",
        unique_id="192.0.2.10:30200",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.ipbuilding.IPBuildingAPI") as mock_api_cls:
        mock_api = mock_api_cls.return_value
        mock_api.get_devices = AsyncMock(return_value=[ipbuilding_button_device])
        mock_api.set_value = AsyncMock(return_value=None)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    await _trigger_button_press(hass, entry.runtime_data.coordinator, ipbuilding_button_device)

    mock_api.set_value.assert_awaited_once()
    args, _kwargs = mock_api.set_value.call_args
    assert args[0] == ipbuilding_button_device["ID"]
    assert args[1] == 1
    assert args[2] == "ON"


async def test_button_press_logs_on_client_error(
    hass: HomeAssistant, mock_setup_entry, ipbuilding_button_device, caplog
) -> None:
    """A network failure during button press should be logged, not raised."""
    import logging

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.0.2.10", CONF_PORT: 30200},
        entry_id="test-button-err",
        unique_id="192.0.2.10:30200",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.ipbuilding.IPBuildingAPI") as mock_api_cls:
        mock_api = mock_api_cls.return_value
        mock_api.get_devices = AsyncMock(return_value=[ipbuilding_button_device])
        mock_api.set_value = AsyncMock(side_effect=ClientError("nope"))
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    with caplog.at_level(logging.WARNING, logger="custom_components.ipbuilding.button"):
        # Should NOT raise — the button platform catches ClientError and warns.
        await _trigger_button_press(
            hass, entry.runtime_data.coordinator, ipbuilding_button_device
        )

    assert any(
        "Failed to press IPBuilding button" in rec.message
        for rec in caplog.records
    )
