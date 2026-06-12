"""Tests for the IPBuilding config flow."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ipbuilding.api import IPBuildingCannotConnect
from custom_components.ipbuilding.const import CONF_HOST, CONF_PORT, DOMAIN


async def test_user_flow_success(hass: HomeAssistant) -> None:
    """A reachable controller should yield a created entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch(
        "custom_components.ipbuilding.config_flow.IPBuildingAPI"
    ) as mock_api_cls:
        mock_api = mock_api_cls.return_value
        mock_api.validate_connection = AsyncMock(return_value=None)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "192.0.2.10", CONF_PORT: 30200},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "IPBuilding (192.0.2.10)"
    assert result["data"] == {CONF_HOST: "192.0.2.10", CONF_PORT: 30200}


async def test_user_flow_cannot_connect(hass: HomeAssistant) -> None:
    """An unreachable controller should surface a cannot_connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.ipbuilding.config_flow.IPBuildingAPI"
    ) as mock_api_cls:
        mock_api = mock_api_cls.return_value
        mock_api.validate_connection = AsyncMock(
            side_effect=IPBuildingCannotConnect("nope")
        )

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "192.0.2.99", CONF_PORT: 30200},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "cannot_connect"


async def test_user_flow_aborts_duplicate(hass: HomeAssistant) -> None:
    """Submitting a host:port that is already configured should abort."""
    MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.0.2.10", CONF_PORT: 30200},
        unique_id="192.0.2.10:30200",
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.ipbuilding.config_flow.IPBuildingAPI"
    ) as mock_api_cls:
        mock_api = mock_api_cls.return_value
        mock_api.validate_connection = AsyncMock(return_value=None)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "192.0.2.10", CONF_PORT: 30200},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
