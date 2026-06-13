"""Tests for the IPBuilding scene platform."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from aiohttp import ClientError
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ipbuilding.const import CONF_HOST, CONF_PORT, DOMAIN


async def test_scene_activate_calls_api(
    hass: HomeAssistant, mock_setup_entry, ipbuilding_scene_device
) -> None:
    """Activating a scene should send value=1, actionType=ON to the controller."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.0.2.10", CONF_PORT: 30200},
        entry_id="test-scene",
        unique_id="192.0.2.10:30200",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.ipbuilding.IPBuildingAPI") as mock_api_cls:
        mock_api = mock_api_cls.return_value
        mock_api.get_devices = AsyncMock(return_value=[ipbuilding_scene_device])
        mock_api.set_value = AsyncMock(return_value=None)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    await hass.services.async_call(
        "scene",
        "turn_on",
        {"entity_id": "scene.movie_night"},
        blocking=True,
    )

    mock_api.set_value.assert_awaited_once()
    args, _kwargs = mock_api.set_value.call_args
    assert args[0] == ipbuilding_scene_device["ID"]
    assert args[1] == 1
    assert args[2] == "ON"


async def test_scene_activate_logs_on_client_error(
    hass: HomeAssistant, mock_setup_entry, ipbuilding_scene_device, caplog
) -> None:
    """A network failure during scene activation should be logged, not raised."""
    import logging

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.0.2.10", CONF_PORT: 30200},
        entry_id="test-scene-err",
        unique_id="192.0.2.10:30200",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.ipbuilding.IPBuildingAPI") as mock_api_cls:
        mock_api = mock_api_cls.return_value
        mock_api.get_devices = AsyncMock(return_value=[ipbuilding_scene_device])
        mock_api.set_value = AsyncMock(side_effect=ClientError("nope"))
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    with caplog.at_level(logging.WARNING, logger="custom_components.ipbuilding.scene"):
        await hass.services.async_call(
            "scene",
            "turn_on",
            {"entity_id": "scene.movie_night"},
            blocking=True,
        )

    assert any(
        "Failed to activate IPBuilding scene" in rec.message
        for rec in caplog.records
    )
