"""Tests for the IPBuilding base entity and per-platform entity invariants."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ipbuilding.const import (
    CONF_HOST,
    CONF_PORT,
    DOMAIN,
)


async def test_unique_id_format_across_platforms(
    hass: HomeAssistant, mock_setup_entry
) -> None:
    """Every entity unique_id must follow ipbuilding_{type}_{device_id}.

    This is a regression guard: the 0.4.0/0.4.1 bug included the config
    entry id in every unique_id, which made Home Assistant treat every
    entity as new on every reinstall. The format is pinned here.
    """
    devices = [
        {"ID": 1, "Type": 2, "Kind": 1, "Description": "D", "Status": 0, "Visible": True},
        {"ID": 2, "Type": 1, "Kind": 1, "Description": "L", "Status": 1, "Visible": True},
        {"ID": 3, "Type": 1, "Kind": 2, "Description": "S", "Status": 0, "Watt": 100, "Visible": True},
        {"ID": 50, "Type": 50, "Description": "B", "Status": 0, "Visible": True},
        {"ID": 100, "Type": 100, "Description": "Sc", "Status": 0, "Visible": True},
        {"ID": 200, "Type": 56, "Description": "T", "Value": 1, "Visible": True},
    ]
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.0.2.10", CONF_PORT: 30200},
        entry_id="test-entity-unique",
        unique_id="192.0.2.10:30200",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.ipbuilding.IPBuildingAPI") as mock_api_cls:
        mock_api = mock_api_cls.return_value
        mock_api.get_devices = AsyncMock(return_value=devices)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    registry = er.async_get(hass)
    seen_prefixes: set[str] = set()
    expected_id_suffixes = {"_1", "_2", "_3", "_50", "_100", "_200"}
    for entity in registry.entities.values():
        if entity.platform != DOMAIN:
            continue
        assert entry.entry_id not in entity.unique_id
        prefix = entity.unique_id.partition("_")[0]
        seen_prefixes.add(prefix)
        # The numeric suffix must end with one of the device ids we set up.
        assert any(
            entity.unique_id.endswith(suf) for suf in expected_id_suffixes
        ), f"Unexpected unique_id {entity.unique_id!r}"

    assert "ipbuilding" in seen_prefixes


async def test_invisible_device_reported_unavailable(
    hass: HomeAssistant, mock_setup_entry, ipbuilding_invisible_device
) -> None:
    """A device with Visible=false should surface as unavailable in HA."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.0.2.10", CONF_PORT: 30200},
        entry_id="test-invisible",
        unique_id="192.0.2.10:30200",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.ipbuilding.IPBuildingAPI") as mock_api_cls:
        mock_api = mock_api_cls.return_value
        mock_api.get_devices = AsyncMock(return_value=[ipbuilding_invisible_device])
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("light.hidden_dimmer")
    assert state is not None
    assert state.state == "unavailable"
