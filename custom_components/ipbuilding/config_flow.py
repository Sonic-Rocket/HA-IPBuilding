"""Config flow for the IPBuilding integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import IPBuildingAPI, IPBuildingCannotConnect, IPBuildingInvalidResponse
from .const import DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
    }
)


class IPBuildingConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for IPBuilding."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step where the user provides the host/port."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            session = async_get_clientsession(self.hass)
            api = IPBuildingAPI(host, port, session)

            try:
                await api.validate_connection()
            except IPBuildingCannotConnect:
                errors["base"] = "cannot_connect"
            except IPBuildingInvalidResponse:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001 - last-resort guard for the UI flow
                _LOGGER.exception("Unexpected error while connecting to IPBuilding")
                errors["base"] = "unknown"
            else:
                # host:port is a stable, human-meaningful identifier for a
                # single controller on the LAN. It is unique within this
                # domain which is what ConfigFlow requires.
                await self.async_set_unique_id(f"{host}:{port}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"IPBuilding ({host})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
