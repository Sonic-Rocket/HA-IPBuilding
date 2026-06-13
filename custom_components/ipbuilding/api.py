"""API Client for IPBuilding."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import DEFAULT_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class IPBuildingAPIError(Exception):
    """Base exception for IPBuilding API errors."""


class IPBuildingCannotConnect(IPBuildingAPIError):
    """Raised when the IPBuilding controller is unreachable."""


class IPBuildingInvalidResponse(IPBuildingAPIError):
    """Raised when the IPBuilding controller returns an unexpected payload."""


class IPBuildingAPI:
    """IPBuilding API Client."""

    def __init__(
        self,
        host: str,
        port: int,
        session: aiohttp.ClientSession,
        timeout: float = DEFAULT_TIMEOUT,
        write_timeout: float = 3.0,
    ) -> None:
        """Initialize the API client."""
        self._host = host
        self._port = port
        self._session = session
        self._timeout = timeout
        self._write_timeout = write_timeout
        self._base_url = f"http://{host}:{port}/api/v1"

    @property
    def host(self) -> str:
        """Return the configured host."""
        return self._host

    @property
    def port(self) -> int:
        """Return the configured port."""
        return self._port

    async def validate_connection(self) -> None:
        """Validate that the controller is reachable.

        Performs a lightweight GET to the device list endpoint and verifies
        that a JSON array is returned. Raises IPBuildingCannotConnect on any
        network failure and IPBuildingInvalidResponse on a malformed payload.
        """
        try:
            await self.get_devices()
        except IPBuildingCannotConnect:
            raise
        except IPBuildingInvalidResponse:
            raise
        except IPBuildingAPIError as err:
            raise IPBuildingCannotConnect(str(err)) from err

    async def get_devices(
        self, types: list[int] | int | None = None
    ) -> list[dict[str, Any]]:
        """Get devices, optionally filtered by type."""
        url = f"{self._base_url}/comp/items"
        params: dict[str, str] = {}
        if types is not None:
            if isinstance(types, list):
                params["types"] = ",".join(str(t) for t in types)
            else:
                params["types"] = str(types)

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.get(url, params=params) as response:
                    response.raise_for_status()
                    data = await response.json(content_type=None)
        except asyncio.TimeoutError as err:
            raise IPBuildingCannotConnect(
                f"Timeout while fetching devices from {self._host}:{self._port}"
            ) from err
        except aiohttp.ClientError as err:
            raise IPBuildingCannotConnect(
                f"Error communicating with API: {err}"
            ) from err

        if not isinstance(data, list):
            if isinstance(data, dict) and "items" in data:
                data = data["items"]
            else:
                data = [data] if data else []

        if types is not None:
            allowed = set(types) if isinstance(types, list) else {types}
            filtered: list[dict[str, Any]] = []
            for d in data:
                dtype = d.get("Type") or d.get("type")
                if dtype is not None and int(dtype) in allowed:
                    filtered.append(d)
            return filtered

        return data

    async def set_value(
        self, device_id: int, value: int, action_type: str | None = None
    ) -> Any:
        """Set a value for a device using the proper action endpoint.

        Uses an HTTP GET request because the IPBuilding REST API only
        accepts GET on ``/action/action``. This was confirmed against a
        live IPBox (firmware returns ``405 Method Not Allowed`` with
        ``Allow: GET`` for POST). The endpoint mutates device state, so
        the URL contains the device id and target value. Callers should
        be aware that URLs may end up in upstream proxy / HA recorder
        logs.
        """
        if action_type is None:
            action_type = "OFF" if value == 0 else "DIM"

        url = f"{self._base_url}/action/action"
        params = {
            "id": device_id,
            "actionType": action_type,
            "value": value,
        }
        try:
            async with asyncio.timeout(self._write_timeout):
                async with self._session.get(url, params=params) as response:
                    response.raise_for_status()
                    return await response.json(content_type=None)
        except asyncio.TimeoutError as err:
            raise IPBuildingCannotConnect(
                f"Timeout while setting value for device {device_id}"
            ) from err
        except aiohttp.ClientError as err:
            raise IPBuildingCannotConnect(
                f"Error setting value for device {device_id}: {err}"
            ) from err
