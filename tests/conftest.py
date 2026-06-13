"""Common pytest fixtures for IPBuilding tests."""
from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.core import HomeAssistant

from custom_components.ipbuilding.const import DOMAIN


@pytest.fixture(autouse=True)
def enable_custom_integrations_fixture(
    enable_custom_integrations: None,
) -> None:
    """Auto-enable the `custom_components` directory for every test.

    The upstream `enable_custom integraties` fixture only empties the loader
    cache; it does not run by default. Wrapping it in an autouse fixture
    here means every test in this repo picks it up without having to
    declare it explicitly, which would otherwise result in
    "Integration not found" errors when the entry-setup tests try to load
    `ipbuilding`.
    """


@pytest.fixture
def mock_setup_entry() -> Generator[None, None, None]:
    """No-op fixture kept for backward compatibility with existing tests.

    Historically this fixture patched either the module-level
    ``async_setup_entry`` or ``ConfigEntries.async_forward_entry_setups`` to
    skip the real entry setup. Patching either of those breaks every test
    that wants to interact with the resulting entities: the first prevents
    ``entry.runtime_data`` from being set, the second prevents the
    platforms from registering entities so service calls fail with
    ``ServiceNotFound``.

    The clean HA-test pattern is to let the real ``async_setup_entry``
    run, mock only the ``IPBuildingAPI`` to avoid hitting a real
    controller, and assert against the resulting entity state. This
    fixture is kept as a no-op so existing tests that take it as a
    parameter keep compiling.
    """


@pytest.fixture
def ipbuilding_devices() -> list[dict]:
    """Return a small set of representative IPBuilding devices."""
    return [
        {
            "ID": 1,
            "Type": 2,  # dimmer
            "Kind": 1,
            "Description": "Kitchen Dimmer",
            "Status": 0,
            "Visible": True,
        },
        {
            "ID": 2,
            "Type": 1,  # relay (light)
            "Kind": 1,
            "Description": "Hallway Light",
            "Status": 1,
            "Visible": True,
        },
        {
            "ID": 3,
            "Type": 1,  # relay (socket)
            "Kind": 2,
            "Description": "Coffee Socket",
            "Status": 0,
            "Watt": 1500,
            "Visible": True,
        },
    ]


@pytest.fixture
def ipbuilding_button_device() -> dict:
    """Return a single IPBuilding button device."""
    return {
        "ID": 50,
        "Type": 50,  # button
        "Description": "Test Button",
        "Status": 0,
        "Visible": True,
    }


@pytest.fixture
def ipbuilding_scene_device() -> dict:
    """Return a single IPBuilding sphere (scene) device."""
    return {
        "ID": 100,
        "Type": 100,  # sphere
        "Description": "Movie Night",
        "Status": 0,
        "Visible": True,
    }


@pytest.fixture
def ipbuilding_sensor_device() -> dict:
    """Return a single IPBuilding time/regime sensor device."""
    return {
        "ID": 200,
        "Type": 56,  # time
        "Description": "System Time",
        "Value": 12345,
        "Visible": True,
    }


@pytest.fixture
def ipbuilding_invisible_device() -> dict:
    """Return a device that the controller reports as not Visible."""
    return {
        "ID": 99,
        "Type": 2,  # dimmer, but hidden
        "Kind": 1,
        "Description": "Hidden Dimmer",
        "Status": 0,
        "Visible": False,
    }
