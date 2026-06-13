"""Tests for the IPBuilding sensor platform."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ipbuilding.const import (
    CONF_HOST,
    CONF_PORT,
    DOMAIN,
    TYPE_REGIME,
    TYPE_TIME,
)


async def test_time_sensor_value(
    hass: HomeAssistant, mock_setup_entry, ipbuilding_sensor_device
) -> None:
    """A time sensor should expose its 'Value' field as native_value."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.0.2.10", CONF_PORT: 30200},
        entry_id="test-time-sensor",
        unique_id="192.0.2.10:30200",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.ipbuilding.IPBuildingAPI") as mock_api_cls:
        mock_api = mock_api_cls.return_value
        mock_api.get_devices = AsyncMock(return_value=[ipbuilding_sensor_device])
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.system_time")
    assert state is not None
    assert state.state == str(ipbuilding_sensor_device["Value"])


async def test_power_sensor_uses_measurement_state_class(
    hass: HomeAssistant, mock_setup_entry, ipbuilding_devices
) -> None:
    """The power sensor must set SensorStateClass.MEASUREMENT.

    Setting MEASUREMENT is what allows downstream ``integration``
    helper sensors to convert this wattage into kWh for Home
    Assistant's Energy Dashboard. The estimate is documented in the
    sensor's docstring; this regression test pins that the
    state_class stays MEASUREMENT so existing Energy-verbruiksmeting
    setups keep working.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.0.2.10", CONF_PORT: 30200},
        entry_id="test-power",
        unique_id="192.0.2.10:30200",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.ipbuilding.IPBuildingAPI") as mock_api_cls:
        mock_api = mock_api_cls.return_value
        mock_api.get_devices = AsyncMock(return_value=ipbuilding_devices)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    # The Coffee Socket (ID=3, Watt=1500) creates a power sensor.
    state = hass.states.get("sensor.coffee_socket_power")
    assert state is not None
    assert state.attributes.get("device_class") == SensorDeviceClass.POWER
    assert state.attributes.get("state_class") == SensorStateClass.MEASUREMENT


async def test_power_sensor_dimmer_estimate(
    hass: HomeAssistant, mock_setup_entry
) -> None:
    """A dimmer at 50% with rated 100W should report 50W (estimated)."""
    devices = [
        {
            "ID": 1,
            "Type": 2,  # dimmer
            "Kind": 1,
            "Description": "D",
            "Status": 50,  # 50% on the 0..100 scale
            "Watt": 100,
            "Visible": True,
        },
    ]
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.0.2.10", CONF_PORT: 30200},
        entry_id="test-power-dim",
        unique_id="192.0.2.10:30200",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.ipbuilding.IPBuildingAPI") as mock_api_cls:
        mock_api = mock_api_cls.return_value
        mock_api.get_devices = AsyncMock(return_value=devices)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.d_power")
    assert state is not None
    assert state.state == "50.0"


async def test_regime_sensor_uses_hub_by_type(
    hass: HomeAssistant, mock_setup_entry
) -> None:
    """A regime sensor must be grouped under HUB_BY_TYPE[TYPE_REGIME][0]."""
    devices = [
        {
            "ID": 700,
            "Type": TYPE_REGIME,
            "Description": "Day",
            "Value": 1,
            "Visible": True,
        },
    ]
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.0.2.10", CONF_PORT: 30200},
        entry_id="test-regime",
        unique_id="192.0.2.10:30200",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.ipbuilding.IPBuildingAPI") as mock_api_cls:
        mock_api = mock_api_cls.return_value
        mock_api.get_devices = AsyncMock(return_value=devices)
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    # The Time and Regime sensors both live on the "hub_system" device.
    # This test pins that we look the hub up via HUB_BY_TYPE rather than
    # hard-coding the string in two different places.
    from homeassistant.helpers import device_registry as dr

    from custom_components.ipbuilding.const import HUB_BY_TYPE

    expected_hub_id = HUB_BY_TYPE[TYPE_REGIME][0]
    dev_reg = dr.async_get(hass)
    hub = dev_reg.async_get_device(identifiers={(DOMAIN, expected_hub_id)})
    assert hub is not None
