"""Common pytest fixtures for IPBuilding tests."""
from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.core import HomeAssistant

from custom_components.ipbuilding.const import DOMAIN


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock, None, None]:
    """Patch async_setup_entry so platforms are not actually loaded."""
    with patch(
        "custom_components.ipbuilding.async_setup_entry",
        return_value=True,
    ) as mock:
        yield mock


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
